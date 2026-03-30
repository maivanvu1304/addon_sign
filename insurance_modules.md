# Insurance Modules Overview

## 1) Pham vi tai lieu

Tai lieu nay tong hop cac module lien quan den nghiep vu `Insurance` trong codebase `d:/Odoo/scg`, gom:

- Nhom module Insurance chinh (co thu muc/module name chua `insurance`)
- Nhom module lien quan gian tiep (API, giao dien, payroll report)

## 2) Mapping menu tren giao dien Insurance

Menu tren man hinh Insurance (Insurance Books, Declaration Insurances, Monthly Summary, Configuration) duoc dinh nghia goc trong:

- `bemo_addons/bemo_hr_insurance/views/menu.xml`

Lop SCG co dieu chinh menu:

- `scg_addons/scg_hr_insurance/views/menu.xml` an 2 menu con:
  - `Past Declaration`
  - `Other Adjustment`

## 3) So do phu thuoc module

```text
bemo_hr_insurance
+- scg_hr_insurance
|  `- aj_insurance_summary
`- bemo_insurance_summary
   `- scg_insurance_summary
      `- aj_insurance_summary
```

Them phu thuoc bo sung:

- `aj_insurance_summary` phu thuoc them `scg_web`
- `bemo_insurance_summary` phu thuoc them `bemo_attendance`, `bemo_time_off`

## 4) Cac module Insurance chinh

### 4.1 `bemo_hr_insurance` (module nen tang)

- Manifest: `bemo_addons/bemo_hr_insurance/__manifest__.py`
- Vai tro:
  - Module core cho nghiep vu bao hiem
  - Tao root menu `Insurance`
  - Quan ly so BH, khai bao tang/giam, tong hop thang, cau hinh
- Depends chinh:
  - `bemo_hr`
  - `bemo_hr_contract`
  - `bemo_payroll`
- Doi tuong/model noi bat:
  - `hr.insurance.book`
  - `hr.insurance.adjustment`
  - `hr.insurance.summary`
  - `hr.insurance.type`
  - `hr.insurance.plan`
  - `hr.insurance.book.history`
- Co cron va report:
  - Cron tao summary, cap nhat so het han
  - Report Aeroo/Excel cho insurance

### 4.2 `scg_hr_insurance` (layer SCG ke thua tu BEMO)

- Manifest: `scg_addons/scg_hr_insurance/__manifest__.py`
- Phu thuoc:
  - `bemo_hr_insurance`
  - `scg_hr`, `scg_hrm`, `scg_hr_contract`
- Dac diem:
  - Ke thua model/view cua `bemo_hr_insurance`
  - Bo sung field nghiep vu SCG (VD: thong tin ho khau/chu ho tren employee)
  - Dieu chinh quy trinh duyet:
    - Them state `to_approve` / Approved cho adjustment/summary
  - Bo sung logic tran muc dong BH theo `hr.insurance.type` (ceiling)
  - An mot so submenu khong su dung

### 4.3 `bemo_insurance_summary` (mo rong Monthly Summary)

- Manifest: `bemo_addons/bemo_insurance_summary/__manifest__.py`
- Phu thuoc:
  - `bemo_hr_insurance`
  - `bemo_attendance`
  - `bemo_time_off`
- Vai tro:
  - Mo rong `hr.insurance.summary` de tinh doi tuong dong/khong dong BH theo ngay cong
  - Them model `hr.insurance.summary.employee`
  - Them field cau hinh:
    - `no_days_not_to_pay_insurance` (nguong ngay khong dong BH)

### 4.4 `scg_insurance_summary` (layer SCG cho Insurance Summary)

- Manifest: `scg_addons/scg_insurance_summary/__manifest__.py`
- Phu thuoc:
  - `bemo_insurance_summary`
- Vai tro:
  - Ke thua `hr.insurance.summary`
  - Bo sung state/flow submit-approve theo SCG
  - Tinh toan lai du lieu summary theo logic attendance/timeoff cua SCG
  - Khong them view/menu moi trong manifest, tap trung vao logic model

### 4.5 `aj_insurance_summary` (layer AJ)

- Manifest: `aj_addons/aj_insurance_summary/__manifest__.py`
- Phu thuoc:
  - `scg_hr_insurance`
  - `scg_insurance_summary`
  - `scg_web`
- Vai tro:
  - Ke thua model/view insurance cho bai toan AJ
  - Bo sung xu ly multi-company:
    - `company_id` tren insurance type/rate/history
    - Rule truy cap theo company
  - Dieu chinh logic `action_load_data` summary cho case AJ (attendance/work shift)
  - Rang buoc unique `code` theo tung company cho `hr.insurance.type`

## 5) Cac module lien quan gian tiep den Insurance

### 5.1 `scg_web`

- File lien quan: `scg_addons/scg_web/static/src/js/views/form/form_controller.js`
- Tac dong:
  - Khoa nut Edit theo state cho:
    - `hr.insurance.adjustment`
    - `hr.insurance.summary`

### 5.2 `scg_rest_api`

- Manifest co khai bao schema:
  - `schemas/hr_insurance_book.xml`
- Co menu mobile API tro den action:
  - `bemo_hr_insurance.action_hr_insurance_book`

### 5.3 `scg_payroll`

- Lien quan den bao cao BH theo thang:
  - `wizard/report_wizard/report_insurance_monthly_wizard.py`
  - `wizard/report_wizard/report_insurance_monthly_wizard_views.xml`
- Co so lieu tong BH tren payslip/payroll approval:
  - `total_social_insurance`

## 6) Goi y stack theo tung boi canh

- Base Insurance toi thieu:
  - `bemo_hr_insurance`
- Stack SCG:
  - `bemo_hr_insurance` + `scg_hr_insurance` + `bemo_insurance_summary` + `scg_insurance_summary`
- Stack AJ:
  - Stack SCG + `aj_insurance_summary`
