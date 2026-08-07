import markdown
import weasyprint
import sys

def main():
    md_file = "MusicXML_Mapping.md"
    pdf_file = "MusicXML_Mapping.pdf"
    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()
    # Convert to HTML
    html_text = markdown.markdown(md_text, extensions=['extra', 'tables'])
    # Add some basic CSS for better PDF
    html_with_style = f'''
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: serif; margin: 40px; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
    </head>
    <body>
    {html_text}
    </body>
    </html>
    '''
    # Write PDF
    weasyprint.HTML(string=html_with_style).write_pdf(pdf_file)
    print(f"PDF written to {pdf_file}")

if __name__ == "__main__":
    main()