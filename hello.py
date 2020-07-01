def hello(event, context):
  print event
  return 'Hello Kubernetes, you said: %s' % event['data']