import asyncio,logging,os,time
from typing import Coroutine
from playwright.async_api import async_playwright,Page,Browser


async def open_chrom(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page=await context.new_page()
        #await page.goto(url)
        input('press any key for close.')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(open_chrom("https://qianwen.aliyun.com/"))
    loop.run_forever()