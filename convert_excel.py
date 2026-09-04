import json
import re
import os
import pdfplumber

def convert_pdf_to_json(pdf_path, json_path):
    students = {}
    
    # Regex nhận diện Mã số sinh viên (chuẩn 10 chữ số)
    mssv_pattern = re.compile(r'\b(\d{10})\b')

    print(f"[+] Đang đọc file PDF: {pdf_path}...")
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row_clean = [cell.strip() if cell else "" for cell in row]
                    row_text = " ".join(row_clean)
                    
                    match = mssv_pattern.search(row_text)
                    if match:
                        mssv = match.group(1)
                        try:
                            ho_ten = row_clean[2] if len(row_clean) > 2 else ""
                            lop = row_clean[3] if len(row_clean) > 3 else ""
                            
                            def get_score(index):
                                if len(row_clean) > index and row_clean[index]:
                                    try:
                                        return float(row_clean[index].replace(',', '.'))
                                    except:
                                        return 0.0
                                return 0.0

                            tc1 = get_score(4)
                            tc2 = get_score(5)
                            tc3 = get_score(6)
                            tc4 = get_score(7)
                            tc5 = get_score(8)
                            
                            tong_diem = get_score(9)
                            if tong_diem == 0.0:
                                tong_diem = tc1 + tc2 + tc3 + tc4 + tc5

                            # Lưu dữ liệu không kèm xếp loại
                            students[mssv] = {
                                "mssv": mssv,
                                "ho_ten": ho_ten,
                                "lop": lop,
                                "tc1": tc1,
                                "tc2": tc2,
                                "tc3": tc3,
                                "tc4": tc4,
                                "tc5": tc5,
                                "tong_diem": tong_diem
                            }
                        except Exception as e:
                            print(f"Lỗi đọc dòng MSSV {mssv}: {e}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(students, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Đã trích xuất thành công {len(students)} sinh viên vào file: {json_path}")

if __name__ == '__main__':
    pdf_file = 'drl_huit.pdf'  # Đổi tên file PDF của bạn vào đây
    output_json = 'data.json'
    
    if os.path.exists(pdf_file):
        convert_pdf_to_json(pdf_file, output_json)
    else:
        print(f"❌ Không tìm thấy file PDF '{pdf_file}'.")