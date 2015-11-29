#!/usr/bin/env python3

import collections
import os
import time

import botocore.session

region_name = os.getenv('EC2_REGION', 'us-west-2')
cluster = os.getenv('ECS_CLUSTER', 'default')

session = botocore.session.get_session()
ecs_client = session.create_client('ecs', region_name=region_name)
ec2_client = session.create_client('ec2', region_name=region_name)

instanceIdToArn = {}
for instanceResponse in ecs_client.get_paginator('list_container_instances').paginate(cluster=cluster):
    for instance in ecs_client.describe_container_instances(cluster=cluster, containerInstances=instanceResponse['containerInstanceArns'])['containerInstances']:
        instanceIdToArn[instance['ec2InstanceId']] = instance['containerInstanceArn']

ArnToPrivateIp = {}
for instanceResponse in ec2_client.get_paginator('describe_instances').paginate(InstanceIds=list(instanceIdToArn.keys())):
    for reservation in instanceResponse['Reservations']:
        for instance in reservation['Instances']:
            ArnToPrivateIp[instanceIdToArn[instance['InstanceId']]] = instance['PrivateIpAddress']

containerToTargets = collections.defaultdict(list)
for serviceResponse in ecs_client.get_paginator('list_services').paginate(cluster=cluster):
    for service in ecs_client.describe_services(cluster=cluster, services=serviceResponse['serviceArns'])['services']:
        serviceName = service['serviceName']
        for taskResponse in ecs_client.get_paginator('list_tasks').paginate(cluster=cluster, serviceName=serviceName):
            for task in ecs_client.describe_tasks(cluster=cluster, tasks=taskResponse['taskArns'])['tasks']:
                for container in task['containers']:
                    for networkBinding in container['networkBindings']:
                        if networkBinding['protocol'] == 'tcp':
                            containerToTargets[container['name']].append('{}:{}'.format(ArnToPrivateIp[task['containerInstanceArn']], networkBinding['hostPort']))

for container, targets in containerToTargets.items():
    print('- targets:')
    for target in targets:
        print('  - {}'.format(target))
    print('  labels:')
    print('    job: {}'.format(container))
print('# {}'.format(time.time()))
