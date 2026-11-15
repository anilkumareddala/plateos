from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime, timedelta
HTML=Path('/mnt/data/plateos-demo/index.html').read_text().replace('    render();\n  })();','    window.__testDB=()=>JSON.parse(JSON.stringify(db));window.__testUpdate86=(id,until)=>{db.item86[locKey()][id]={until,at:Date.now()};save();render()};render();\n  })();')
with sync_playwright() as p:
 b=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 pg=b.new_page(viewport={'width':1512,'height':980},device_scale_factor=1)
 pg.route('**/*',lambda r:r.abort())
 errors=[]
 pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.set_content(HTML,wait_until='domcontentloaded')
 assert not errors,errors
 assert pg.locator('[data-mode=menu]').count()==1
 def db():return pg.evaluate("window.__testDB()")
 def tab(t):pg.locator(f'[data-mode={t}]').first.click()
 tab('menu')
 assert pg.locator('h1').first.inner_text()=='Dynamic menu manager'
 print('menu items',pg.locator('.ops-item-row').count())
 assert pg.locator('.ops-item-row').count()>=8
 pg.screenshot(path='/mnt/data/plateos-demo/preview-ops-menu.png',full_page=True)
 # 86 immediate + timed auto expiry
 pg.locator('[data-action=ops-open-86][data-id=smash-burger]').click()
 assert '86' in pg.locator('.ops-dialog h2').inner_text()
 pg.locator('[data-action=ops-86-confirm][data-period=manual]').click()
 assert '86' in pg.locator('.ops-item-row:has-text("Double Smash Burger")').inner_text()
 assert not db()['item86']['juniper:uptown']['smash-burger']['until']
 tab('kiosk')
 pg.locator('#daypart-select').select_option('Late-Night')
 assert pg.locator('.food-card:has-text("Double Smash Burger") .add-square').is_disabled()
 tab('pos')
 pg.locator('[data-action=pos-service][data-service="Dine in"]').click();pg.locator('[data-action=pos-table-open][data-table="04"]').click()
 pg.locator('#daypart-select').select_option('Late-Night')
 assert pg.locator('.food-card:has-text("Double Smash Burger") .add-square').is_disabled()
 tab('menu')
 pg.locator('[data-action=ops-open-86][data-id=smash-burger]').click()
 # Restore is one-tap from the menu list, without another modal
 assert 'Available' in pg.locator('.ops-item-row:has-text("Double Smash Burger")').inner_text()
 # expired record auto-available, even when underlying record exists
 pg.evaluate("window.__testUpdate86('smash-burger',Date.now()-1000)")
 # rehydrate with selector switch (same location persisted)
 pg.locator('#location-select').select_option('plano');pg.locator('#location-select').select_option('uptown')
 assert 'Available' in pg.locator('.ops-item-row:has-text("Double Smash Burger")').inner_text()
 # Item CRUD: create dinner item with required modifier group
 pg.locator('[data-action=ops-new-item]').click()
 pg.locator('#ops-item-name').fill('Smoked Mushroom Plate')
 pg.locator('#ops-item-id').fill('smoked-mushroom')
 pg.locator('#ops-item-price').fill('18.75')
 pg.locator('#ops-item-required').select_option(label='Spice level')
 pg.locator('#ops-item-start').fill('10:00')
 pg.locator('#ops-item-end').fill('23:59')
 pg.locator('input[data-ops-item-day="Dinner"]').check()
 pg.locator('input[data-ops-item-day="Late-Night"]').check()
 pg.locator('[data-action=ops-save-item]').click()
 assert any(x['id']=='smoked-mushroom' for x in db()['menuCatalog']['juniper'])
 assert db()['itemHours']['juniper:uptown']['smoked-mushroom']=={'start':'10:00','end':'23:59'}
 # price override on edited item
 pg.locator('[data-action=ops-edit-item][data-id=smoked-mushroom]').click()
 pg.locator('#ops-item-override').fill('21.50')
 pg.locator('[data-action=ops-save-item]').click()
 assert db()['priceOverrides']['juniper:uptown']['smoked-mushroom']==21.5
 # category add/rename, modifier group add/change
 pg.locator('[data-action=ops-menu-tab][data-tab=categories]').click()
 pg.locator('[data-action=ops-new-category]').click()
 pg.locator('#ops-category-name').fill('Chef Specials')
 pg.locator('[data-action=ops-save-category]').click()
 assert any(c['name']=='Chef Specials' for c in db()['menuCategories']['juniper'])
 pg.locator('[data-action=ops-menu-tab][data-tab=modifiers]').click()
 pg.locator('[data-action=ops-new-group]').click()
 pg.locator('#ops-group-name').fill('Temperature')
 pg.locator('#ops-group-options').fill('Rare | 0\nMedium | 0\nWell Done | 0')
 pg.locator('[data-action=ops-save-group]').click()
 assert any(g['name']=='Temperature' for g in db()['modifierGroups']['juniper'])
 # daypart hour update
 pg.locator('[data-action=ops-menu-tab][data-tab=hours]').click()
 pg.locator('[data-ops-day="Breakfast"][data-ops-bound="end"]').fill('10:30')
 pg.locator('[data-ops-day="Breakfast"][data-ops-bound="end"]').dispatch_event('change')
 assert db()['daypartSchedules']['juniper:uptown']['Breakfast']['end']=='10:30'
 pg.screenshot(path='/mnt/data/plateos-demo/preview-ops-hours.png',full_page=True)
 # timecards, tips
 tab('staff')
 assert pg.locator('h1').first.inner_text()=='People, timecards & labor'
 assert pg.locator('.ops-stat').count()==4
 assert pg.locator('[data-action=ops-edit-punch]').count()>=3
 pg.screenshot(path='/mnt/data/plateos-demo/preview-ops-people.png',full_page=True)
 orig=db()['timeEvents'][0]['at']
 ev_id=pg.locator('[data-action=ops-edit-punch]').first.get_attribute('data-id')
 selected=[x for x in db()['timeEvents'] if x['id']==ev_id][0]
 pg.locator('[data-action=ops-edit-punch]').first.click()
 pg.locator('#ops-punch-newtime').fill('2026-11-13T12:34')
 pg.locator('#ops-punch-reason').fill('Missed punch confirmed against schedule')
 pg.locator('[data-action=ops-save-correction]').click()
 assert [x for x in db()['timeEvents'] if x['id']==ev_id][0]['at']==selected['at'], 'Original punch overwritten!'
 assert len([x for x in db()['timeCorrections'] if x['eventId']==ev_id])==1
 pg.locator(f'[data-action=ops-history][data-id="{ev_id}"]').click()
 assert 'Original' in pg.locator('.ops-dialog').inner_text()
 assert 'Revision 1' in pg.locator('.ops-dialog').inner_text()
 pg.locator('[data-action=ops-close]').click()
 pg.locator('[data-action=ops-people-tab][data-tab=tips]').click()
 assert 'Card tips in pool' in pg.locator('main').inner_text()
 assert 'CASH SHARE' in pg.locator('main').inner_text()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-ops-tips.png',full_page=True)
 # PIN timeclock valid staff clock out based on seeded server in
 pg.locator('[data-action=ops-clock-open]').first.click()
 pg.locator('#ops-clock-pin').fill('4004')
 pg.locator('[data-action=ops-clock-punch][data-type=out]').click()
 assert db()['timeEvents'][-1]['type']=='out'
 # Cashier role restricted view
 pg.locator('#ops-actor-top').select_option('juniper-cashier')
 assert pg.locator('[data-mode=menu]').count()==0
 assert pg.locator('[data-mode=staff]').count()==0
 assert pg.locator('[data-mode=reports]').count()==0
 assert pg.locator('h1').first.inner_text()=='POS register & server handheld'
 # Void unsent item triggers approval
 pg.locator('[data-action=pos-service][data-service="Dine in"]').click();pg.locator('[data-action=pos-table-open][data-table="04"]').click()
 assert pg.locator('[data-action=ops-void]').count()>0
 before=len(db()['securityEvents'])
 pg.locator('[data-action=ops-void]').first.click()
 assert 'Manager approval required' in pg.locator('.ops-dialog').inner_text()
 pg.locator('#ops-approval-pin').fill('9999')
 pg.locator('#ops-approval-reason').fill('Guest changed mind after entry')
 pg.locator('[data-action=ops-approve]').click()
 assert 'invalid' in pg.locator('.toast').inner_text().lower()
 assert len(db()['securityEvents'])==before
 pg.locator('#ops-approval-pin').fill('2002')
 pg.locator('[data-action=ops-approve]').click()
 assert len(db()['securityEvents'])==before+1
 assert db()['securityEvents'][-1]['action']=='Void item'
 assert db()['securityEvents'][-1]['initiatedBy']=='juniper-cashier'
 assert db()['securityEvents'][-1]['approvedBy']=='juniper-manager'
 print('approved void',db()['securityEvents'][-1])
 # Big discount required approval and audited
 pg.locator('[data-action=ops-discount]').click()
 pg.locator('#ops-approval-pin').fill('2002')
 pg.locator('#ops-approval-reason').fill('Service recovery approved by manager')
 pg.locator('[data-action=ops-approve]').click()
 assert db()['securityEvents'][-1]['action']=='Large discount (20%)'
 assert db()['checks'] and any(c.get('discountApplied') for c in db()['checks'])
 # Drawer event
 pg.locator('[data-action=ops-open-drawer]').first.click()
 pg.locator('#ops-drawer-type').select_option('Paid-Out')
 pg.locator('#ops-drawer-amount').fill('13.25')
 pg.locator('[data-action=ops-drawer-submit]').click()
 pg.locator('#ops-approval-pin').fill('2002')
 pg.locator('#ops-approval-reason').fill('Refund petty cash for supplies')
 pg.locator('[data-action=ops-approve]').click()
 assert db()['cashEvents'][-1]['amountCents']==1325
 # Refund event
 pg.locator('[data-action=ops-open-refunds]').first.click()
 pg.locator('input[name=ops-refund-payment]').first.check()
 pg.locator('[data-action=ops-refund-submit]').click()
 pg.locator('#ops-approval-pin').fill('2002')
 pg.locator('#ops-approval-reason').fill('Duplicate ticket order refunded')
 pg.locator('[data-action=ops-approve]').click()
 assert len(db()['refunds'])==1
 # manager security log
 pg.locator('#ops-actor-top').select_option('juniper-manager')
 tab('security')
 assert pg.locator('h1').first.inner_text()=='Security activity & approvals'
 assert pg.locator('tr').count()>=5
 assert 'Void item' in pg.locator('main').inner_text()
 assert 'Cash drawer Paid-Out' in pg.locator('main').inner_text()
 assert 'Payment refund' in pg.locator('main').inner_text()
 pg.screenshot(path='/mnt/data/plateos-demo/preview-ops-security.png',full_page=True)
 # Tenant isolation
 pg.locator('#brand-select').select_option('saffron')
 tab('security')
 assert 'Void item' not in pg.locator('main').inner_text()
 assert db()['securityEvents'][-1]['brandId']=='juniper'
 # Mobile view testing
 mobile=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
 mobile.route('**/*',lambda r:r.abort())
 mobile.set_content(HTML)
 print('mobile width',mobile.evaluate('document.documentElement.scrollWidth'),mobile.evaluate('window.innerWidth'))
 assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 mobile.locator('[data-action=side-open]').click()
 assert mobile.locator('#ops-actor-sidebar').is_visible()
 mobile.locator('#ops-actor-sidebar').select_option('juniper-manager')
 mobile.locator('[data-mode=menu]').first.click()
 mobile.screenshot(path='/mnt/data/plateos-demo/preview-ops-mobile.png',full_page=True)
 assert not errors,errors
 print('SUCCESS v4 back-office ops E2E tests passed')
 b.close()
