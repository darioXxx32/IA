$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$evidence = Join-Path $PSScriptRoot 'evidencias'

Write-Host '=== Python syntax ==='
python -m py_compile `
  (Join-Path $root 'python-basic\producer.py') `
  (Join-Path $root 'python-basic\consumer.py') `
  (Join-Path $root 'python-pubsub\pub.py') `
  (Join-Path $root 'python-pubsub\sub.py')
Write-Host 'PASS: all four Python scripts compile.'

Write-Host '=== RabbitMQ AMQP connectivity ==='
python -c "import pika; c=pika.BlockingConnection(pika.ConnectionParameters('localhost')); print('PASS: connected to localhost:5672'); c.close()"

Write-Host '=== Queue producer ==='
$pythonBasic = Join-Path $root 'python-basic'
$consumerOut = Join-Path $evidence 'activity1-python-consumer.stdout.txt'
$consumerErr = Join-Path $evidence 'activity1-python-consumer.stderr.txt'
$consumer = Start-Process -FilePath python -ArgumentList '-u consumer.py' -WorkingDirectory $pythonBasic `
  -PassThru -WindowStyle Hidden -RedirectStandardOutput $consumerOut -RedirectStandardError $consumerErr
try {
  Start-Sleep -Seconds 2
  python (Join-Path $pythonBasic 'producer.py')
  Start-Sleep -Seconds 1
} finally {
  if (-not $consumer.HasExited) { Stop-Process -Id $consumer.Id -Force }
}
Get-Content $consumerOut

Write-Host '=== Fanout delivery to two independent queues ==='
python -c "import pika; c=pika.BlockingConnection(pika.ConnectionParameters('localhost')); ch=c.channel(); ch.exchange_declare(exchange='logs',exchange_type='fanout',durable=True); a=ch.queue_declare(queue='',exclusive=True).method.queue; b=ch.queue_declare(queue='',exclusive=True).method.queue; ch.queue_bind(exchange='logs',queue=a); ch.queue_bind(exchange='logs',queue=b); ch.basic_publish(exchange='logs',routing_key='',body=b'Workshop6 fanout test'); x=ch.basic_get(a,auto_ack=True)[2].decode(); y=ch.basic_get(b,auto_ack=True)[2].decode(); print('subscriber 1:',x); print('subscriber 2:',y); assert x==y=='Workshop6 fanout test'; print('PASS: both subscribers received the broadcast'); c.close()"

Write-Host '=== Broker queue state ==='
docker exec workshop6-rabbitmq rabbitmqctl list_queues name messages consumers

Write-Host '=== Install librabbitmq-dev in the reproducible Ubuntu build image and compile C ==='
$cSource = (Resolve-Path (Join-Path $root 'c-basic')).Path
$dockerfile = Join-Path $PSScriptRoot 'c-basic\Dockerfile'
docker build -t workshop6-c-dev -f $dockerfile (Join-Path $root 'c-basic')
docker run --rm -v "${cSource}:/work" -w /work workshop6-c-dev make

Write-Host '=== C consumer + producer integration ==='
$oldConsumer = docker ps -aq --filter 'name=^workshop6-c-consumer$'
if ($oldConsumer) { docker rm -f workshop6-c-consumer | Out-Null }
docker run -d --name workshop6-c-consumer --add-host=host.docker.internal:host-gateway `
  -v "${cSource}:/work" -w /work -e RABBITMQ_HOST=host.docker.internal `
  workshop6-c-dev sh -lc 'stdbuf -oL ./c_consumer' | Out-Null
Start-Sleep -Seconds 2
docker run --rm --add-host=host.docker.internal:host-gateway -v "${cSource}:/work" `
  -w /work -e RABBITMQ_HOST=host.docker.internal workshop6-c-dev ./c_producer
Start-Sleep -Seconds 1
$cOutput = docker logs workshop6-c-consumer
$cOutput | Set-Content -Encoding utf8 (Join-Path $evidence 'activity1-c-consumer.txt')
$cOutput
docker stop workshop6-c-consumer | Out-Null
docker rm workshop6-c-consumer | Out-Null

Write-Host "Evidence folder: $evidence"
