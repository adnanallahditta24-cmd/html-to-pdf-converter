from flask import Flask, request, send_file
from playwright.async_api import async_playwright
import asyncio
import os
import tempfile
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allows your Netlify frontend to talk to this backend

async def run_conversion(html_content):
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--no-sandbox'])
        page = await browser.new_page()
        
        # Set content directly
        await page.set_content(html_content, wait_until="networkidle")
        await page.emulate_media(media="screen")
        
        # Get dynamic dimensions for perfect fit
        dimensions = await page.evaluate('''() => {
            return {
                width: document.documentElement.offsetWidth,
                height: document.documentElement.offsetHeight,
            }
        }''')

        pdf_path = os.path.join(tempfile.gettempdir(), "output.pdf")
        await page.pdf(
            path=pdf_path,
            print_background=True,
            width=f"{dimensions['width']}px",
            height=f"{dimensions['height'] + 50}px",
            margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"}
        )
        await browser.close()
        return pdf_path

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files['file']
    html_string = file.read().decode('utf-8')
    
    # Run the async conversion in a loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    pdf_file = loop.run_until_complete(run_conversion(html_string))
    
    return send_file(pdf_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
