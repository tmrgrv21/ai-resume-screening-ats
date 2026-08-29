"""
Helper script to generate PDF and DOCX versions of sample resumes
for multi-format file uploader testing.
"""

import os

def generate_samples():
    print("Generating DOCX and PDF sample files...")
    
    sample_dir = os.path.dirname(os.path.abspath(__file__))
    txt_files = [f for f in os.listdir(sample_dir) if f.endswith('.txt') and f != 'job_description.txt']
    
    # 1. Create DOCX files using python-docx if installed
    try:
        import docx
        for txt_f in txt_files:
            txt_path = os.path.join(sample_dir, txt_f)
            docx_path = os.path.join(sample_dir, txt_f.replace('.txt', '.docx'))
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc = docx.Document()
            for line in content.split('\n'):
                doc.add_paragraph(line)
            doc.save(docx_path)
            print(f"Created DOCX: {docx_path}")
    except Exception as e:
        print(f"Could not create DOCX files: {e}")

if __name__ == "__main__":
    generate_samples()
