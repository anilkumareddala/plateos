from playwright.sync_api import sync_playwright
from subprocess import Popen, DEVNULL
from pathlib import Path
from time import sleep
from urllib.request import urlopen
import os
SERVER='http://127.0.0.1:8890/index.html'
p=Popen(['python3','-m','http.server','8890','--bind','127.0.0.1'],cwd='/mnt/data/plateos-demo',stdout=DEVNULL,stderr=DEVNULL)
try:
 for _ in range(30):
  try:
   urlopen(SERVER,timeout=1);break
  except Exception:sleep(.15)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  ctx=browser.new_context(viewport={'width':1350,'height':900})
  first=ctx.new_page();second=ctx.new_page()
  errors=[]
  first.on('pageerror',lambda e:errors.append('first '+str(e)))
  second.on('pageerror',lambda e:errors.append('second '+str(e)))
  for page in (first,second):
   page.route('https://**/*',lambda r:r.abort())
   page.goto(SERVER,wait_until='domcontentloaded')
   page.locator('[data-mode=queue]').first.click()
  before=second.locator('.omni-order-row').count()
  first.locator('#omni-demo-channel').select_option('Website')
  first.locator('#omni-demo-item').select_option('smash-burger')
  first.locator('[data-action=omni-inject]').click()
  second.wait_for_timeout(200)
  print('BROADCAST QUEUE',before,second.locator('.omni-order-row').count())
  assert second.locator('.omni-order-row').count()==before+1
  # device cross-tab presence
  for page in (first,second):page.locator('[data-mode=devices]').first.click()
  first.locator('[data-action=omni-test-print]').first.click()
  assert 'Test print #1' in second.locator('.omni-device-logs').inner_text()
  # offline POS event does not show in KDS until reconnection
  first.locator('[data-mode=floor]').first.click()
  first.locator('[data-action=omni-open-table][data-table="02"]').first.click()
  first.locator('[data-action=pos-offline]').first.click()
  first.locator('[data-action=item][data-id=smash-burger]').first.click()
  first.locator('input[name=required]').first.check()
  first.locator('#pos-item-note').fill('No onions - cross-tab offline test')
  first.locator('[data-action=modal-add]').click()
  first.locator('[data-action=pos-send]').click()
  assert 'queued' in first.locator('.pos-offline-banner').inner_text().lower()
  second.locator('[data-mode=kds]').first.click()
  assert 'No onions - cross-tab offline test' not in second.locator('main').inner_text()
  first.locator('[data-action=pos-offline]').first.click()
  second.wait_for_timeout(200)
  assert 'No onions - cross-tab offline test' in second.locator('main').inner_text()
  print('OFFLINE SYNC visible exactly after restore')
  assert not errors,errors
  browser.close()
finally:
 p.terminate();p.wait(timeout=5)
