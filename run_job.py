#!/usr/bin/env python3

import sys
import requests
from time import sleep
from requests.auth import HTTPBasicAuth
from json import loads, dumps

# GET /api/v2/ping/
# GET /api/v2/job_templates/
# POST /api/v2/job_templates/{template_id}/launch/
# GET /api/v2/jobs/{job_id}/

template_id = 10
tls_verify = False
host_url = 'http://192.168.49.2:30080/api/v2'
ob_user = 'opsbridge_demo'
ob_password = 'opsbridge_demo'

def bstr_to_dict(bstr):
  s = bstr.decode('UTF-8', errors='strict')
  return loads(s)

def job_execute(template_id: str):
  url = f'{host_url}/job_templates/{template_id}/launch/'
  print(url)
  return requests.post(
    url,
    verify=tls_verify,
    auth=HTTPBasicAuth(ob_user, ob_password)
  )

if __name__ == '__main__':
  if len(sys.argv) == 1:
    job_id = str(int(sys.argv[1]))
  else:
    job_id = str(template_id)
  if True:
    job = bstr_to_dict(job_execute(template_id).content)
    print(dumps(job))
    #exit(0)
    job_id = job['id']
    print(f'please wait for job {job_id} to finish')
    sleep(1.0)
    result = requests.get(
      f'{host_url}/jobs/{job_id}/',
      verify=tls_verify,
      auth=HTTPBasicAuth(ob_user, ob_password)
    )
    status = bstr_to_dict(result.content)
    #print(dumps(status))
    if status['finished']: print('finished: ' + str(status['finished']))
    while not status['finished']:
      sleep(1.0)
      result = requests.get(
        f'{host_url}/jobs/{job_id}/',
        verify=tls_verify,
        auth=HTTPBasicAuth(ob_user, ob_password)
      )
      status = bstr_to_dict(result.content)
      #print(dumps(status))
      if status['finished']: print('finished: ' + str(status['finished']))
    print(dumps(status))
