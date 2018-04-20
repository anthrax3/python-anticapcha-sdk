# python-anticapcha-sdk
Python library for working with anti-captcha.com

# Usage example:
```python
from captcha import *
from time import sleep

# For first, we need to create captcha service.
service = AntiCaptchaService(client_key='ANTI_CAPTCHA_KEY')

# Let's check account balance
print('Current balance: {}'.format(service.get_balance()))

# If all is ok, we can continue with solving captchas
# We need to create instance of required task, i will 
# use image-to-text captcha task builder that accepts 
# only letters and matches case.
task = ImageToTextTask(image_url='CAPCHA_IMAGE_ADDRESS', numeric=Numeric.ONLY_LETTERS, case=True)
task = service.create_task(task, LanguagePool.RUSSIAN)

# Our task was created and sent to service, so we need 
# to wait a while when captcha will be solved.
while True:
  result = service.get_task_result(task)
  if result['status']:
    break
  sleep(1)

# Done!
print('Captcha solved: {}'.format(result['solution']['text']))
```
