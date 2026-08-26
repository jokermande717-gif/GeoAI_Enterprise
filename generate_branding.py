import os

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="geoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="50%" stop-color="#0284c7" />
      <stop offset="100%" stop-color="#0c4a6e" />
    </linearGradient>
    <linearGradient id="meshGrad" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.85" />
    </linearGradient>
  </defs>
  <polygon points="256,40 440,140 440,372 256,472 72,372 72,140" fill="#0f172a" stroke="url(#geoGrad)" stroke-width="14" stroke-linejoin="round" />
  <polygon points="256,40 256,256 72,140" fill="url(#meshGrad)" opacity="0.4" />
  <polygon points="256,40 440,140 256,256" fill="url(#meshGrad)" opacity="0.6" />
  <polygon points="72,140 256,256 72,372" fill="url(#meshGrad)" opacity="0.5" />
  <polygon points="440,140 440,372 256,256" fill="url(#meshGrad)" opacity="0.7" />
  <polygon points="72,372 256,472 256,256" fill="url(#meshGrad)" opacity="0.9" />
  <polygon points="440,372 256,472 256,256" fill="url(#meshGrad)" opacity="0.8" />
  <line x1="256" y1="40" x2="256" y2="472" stroke="#38bdf8" stroke-width="4" stroke-linecap="round" />
  <line x1="72" y1="140" x2="440" y2="372" stroke="#38bdf8" stroke-width="3" stroke-dasharray="6,6" opacity="0.7" />
  <line x1="72" y1="372" x2="440" y2="140" stroke="#38bdf8" stroke-width="3" stroke-dasharray="6,6" opacity="0.7" />
  <circle cx="256" cy="40" r="10" fill="#38bdf8" />
  <circle cx="440" cy="140" r="10" fill="#38bdf8" />
  <circle cx="440" cy="372" r="10" fill="#38bdf8" />
  <circle cx="256" cy="472" r="10" fill="#38bdf8" />
  <circle cx="72" cy="372" r="10" fill="#38bdf8" />
  <circle cx="72" cy="140" r="10" fill="#38bdf8" />
  <circle cx="256" cy="256" r="14" fill="#ffffff" />
</svg>'''

with open("logo.svg", "w", encoding="utf-8") as f:
    f.write(svg_code)

print("[✓] تم إنشاء logo.svg بنجاح.")

# محاولة توليد PNG و ICO إذا كانت مكتبة Pillow متوفرة
try:
    from PIL import Image, ImageDraw
    # رسم بديل عالي الدقة وتصدير ICO
    img = Image.new("RGBA", (256, 256), (15, 23, 42, 255))
    draw = ImageDraw.Draw(img)
    # رسم مضلع وإطارات هندسية
    draw.polygon([(128, 20), (220, 70), (220, 186), (128, 236), (36, 186), (36, 70)], outline=(56, 189, 248), width=6)
    draw.line([(128, 20), (128, 236)], fill=(56, 189, 248), width=3)
    draw.line([(36, 70), (220, 186)], fill=(2, 132, 199), width=2)
    draw.line([(36, 186), (220, 70)], fill=(2, 132, 199), width=2)
    draw.ellipse([(120, 120), (136, 136)], fill=(255, 255, 255))
    
    img.save("logo.png", format="PNG")
    img.save("app_icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("[✓] تم إنشاء logo.png و app_icon.ico بنجاح.")
except ImportError:
    print("[!] يرجى تثبيت Pillow لتوليد ICO عبر: pip install pillow")