import base64

source_file = "web/index.html"
output_file = "web/index.prod.html"

with open(source_file, "r", encoding="utf-8") as f:
    raw_html = f.read()

encoded = base64.b64encode(raw_html.encode('utf-8')).decode('utf-8')

protected_wrapper = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>GeoAI OVERLORD // Sovereign Protected Core</title>
<meta name="robots" content="noindex, nofollow">
<script>
document.addEventListener('contextmenu', e => e.preventDefault());
document.onkeydown = function(e) {{
    if (e.keyCode == 123 || (e.ctrlKey && e.shiftKey && (e.keyCode == 73 || e.keyCode == 74)) || (e.ctrlKey && e.keyCode == 85)) {{
        return false;
    }}
}};
</script>
</head>
<body>
<script>
const _0xcore = "{encoded}";
document.open();
document.write(decodeURIComponent(escape(window.atob(_0xcore))));
document.close();
</script>
</body>
</html>"""

with open(output_file, "w", encoding="utf-8") as f:
    f.write(protected_wrapper)

print(f"✓ Production Encrypted HTML Ready: {output_file}")
