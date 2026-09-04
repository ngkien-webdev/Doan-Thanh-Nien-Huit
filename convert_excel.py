import os
import pandas as pd
import json
import math

# Hàm xử lý điểm an toàn, chặn lỗi NaN
def clean_float(val):
    try:
        v = float(str(val).replace(',', '.').strip())
        return 0.0 if math.isnan(v) else v
    except:
        return 0.0

def excel_folder_to_json(folder_path, output_json_path):
    students = {}
    
    # Các tên sheet hoặc từ khóa muốn BỎ QUA không đọc
    ignored_sheets = ["ĐÚNG THÔNG TIN", "HƯỚNG DẪN", "NOTE", "LƯU Ý", "CHUẨN"]

    if not os.path.exists(folder_path):
        print(f"Không tìm thấy thư mục {folder_path}")
        return

    for file_name in os.listdir(folder_path):
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')) or file_name.startswith('~'):
            continue
            
        file_path = os.path.join(folder_path, file_name)
        print(f"\n[+] Đang xử lý file: {file_name}...")
        
        try:
            excel_file = pd.ExcelFile(file_path)
            all_sheets = excel_file.sheet_names
        except Exception as e:
            print(f"  -> Lỗi đọc file {file_name}: {e}")
            continue

        for sheet_name in all_sheets:
            # Kiểm tra nếu tên sheet nằm trong danh sách cần bỏ qua
            sheet_upper = sheet_name.strip().upper()
            if any(ignore in sheet_upper for ignore in ignored_sheets):
                print(f"  -> [!] Bỏ qua sheet rác/hướng dẫn: {sheet_name}")
                continue
                
            print(f"  -> Đọc sheet hoạt động: {sheet_name}")
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            
            header_row_idx = -1
            for idx, row in df_raw.iterrows():
                row_vals = [str(val).strip().upper().replace('\n', '', ).replace(' ', '') for val in row.values]
                if 'MSSV' in row_vals or 'MÃSỐSINHVIÊN' in row_vals:
                    header_row_idx = idx
                    break
            
            if header_row_idx == -1:
                print(f"     [!] Bỏ qua sheet '{sheet_name}' (không tìm thấy cột MSSV)")
                continue
                
            df = df_raw.iloc[header_row_idx+1:].copy()
            raw_headers = df_raw.iloc[header_row_idx].values
            headers = [str(val).strip().upper().replace('\n', '').replace(' ', '') for val in raw_headers]
            
            mssv_idx, ho_ten_idx, lop_idx, diem_cong_idx, diem_tru_idx, ghi_chu_idx = -1, -1, -1, -1, -1, -1
            
            for i, col in enumerate(headers):
                if 'MSSV' in col or 'MÃSỐ' in col:
                    if mssv_idx == -1: mssv_idx = i
                elif 'HỌVÀTÊN' in col or 'HỌTÊN' in col:
                    if ho_ten_idx == -1: ho_ten_idx = i
                elif 'LỚP' in col:
                    if lop_idx == -1: lop_idx = i
                elif 'CỘNG' in col:
                    if diem_cong_idx == -1: diem_cong_idx = i
                elif 'TRỪ' in col:
                    if diem_tru_idx == -1: diem_tru_idx = i
                elif 'GHICHÚ' in col:
                    if ghi_chu_idx == -1: ghi_chu_idx = i
            
            if mssv_idx == -1:
                continue

            for _, row in df.iterrows():
                try:
                    mssv = str(row.iloc[mssv_idx]).strip()
                    
                    if not mssv or mssv.lower() == 'nan' or mssv == 'None' or len(mssv) > 15 or 'trưởng' in mssv.lower() or 'người' in mssv.lower():
                        continue
                    
                    ho_ten = ""
                    if ho_ten_idx != -1:
                        ho = str(row.iloc[ho_ten_idx]).strip()
                        if ho.lower() == 'nan': ho = ''
                        ten = ""
                        if ho_ten_idx + 1 < len(headers) and headers[ho_ten_idx + 1] == 'NAN':
                            ten_val = str(row.iloc[ho_ten_idx + 1]).strip()
                            if ten_val.lower() != 'nan':
                                ten = ten_val
                        ho_ten = f"{ho} {ten}".strip()
                    
                    lop = ""
                    if lop_idx != -1:
                        lop = str(row.iloc[lop_idx]).strip()
                        if lop.lower() == 'nan': lop = ''
                    
                    diem_cong = clean_float(row.iloc[diem_cong_idx]) if diem_cong_idx != -1 else 0.0
                    diem_tru = clean_float(row.iloc[diem_tru_idx]) if diem_tru_idx != -1 else 0.0
                    
                    ghi_chu = ""
                    if ghi_chu_idx != -1:
                        ghi_chu = str(row.iloc[ghi_chu_idx]).strip()
                        if ghi_chu.lower() == 'nan': ghi_chu = ''
                    
                    if mssv not in students:
                        students[mssv] = {
                            "mssv": mssv,
                            "ho_ten": ho_ten,
                            "lop": lop,
                            "tong_diem": 0.0,
                            "chi_tiet": []
                        }
                    
                    students[mssv]["tong_diem"] += (diem_cong - diem_tru)
                    students[mssv]["chi_tiet"].append({
                        "nguon": f"{file_name.replace('.xlsx', '').replace('.xls', '')}",
                        "hoat_dong": sheet_name,
                        "diem_cong": diem_cong,
                        "diem_tru": diem_tru,
                        "ghi_chu": ghi_chu
                    })
                except Exception as ex:
                    continue

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(students, f, ensure_ascii=False, indent=4, allow_nan=False)
    print(f"\n✅ Xử lý hoàn tất. Đã lưu file: {output_json_path}")

if __name__ == '__main__':
    if not os.path.exists('du_lieu_excel'):
        os.makedirs('du_lieu_excel')
    else:
        excel_folder_to_json('du_lieu_excel', 'data.json')