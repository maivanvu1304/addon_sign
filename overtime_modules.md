# Overtime Modules Overview

## 1) Pham vi tai lieu

Tai lieu nay tong hop cac module lien quan den nghiep vu `Overtime` trong codebase `d:/Odoo/scg`, gom:

- Nhom module OT chinh (office OT, shift OT, project OT)
- Nhom module tich hop lien quan (API, payroll, dashboard, notification)

## 2) Mapping menu Overtime tren giao dien

Menu tren giao dien nhu man hinh ban gui (`Overtime for Office`, `Overtime for Shift`, `Import`, `Reporting`, `Configuration`) duoc hinh thanh theo cac lop:

- Lop goc BEMO (tao root menu `Overtime`):
  - `bemo_addons/bemo_hr_overtime/views/menu.xml`
- Lop SCG (them `Reporting`, `Import`, doi ten 1 so submenu):
  - `scg_addons/scg_hr_overtime/views/menu.xml`
  - `scg_addons/scg_hr_overtime/data/menu.xml`
- Lop AJ (them nhanh OT theo ca, doi ten menu office):
  - `aj_addons/aj_workshift_overtime/views/menu.xml`

## 3) So do phu thuoc module OT chinh

```text
bemo_hr_overtime
+- scg_hr_overtime
|  +- aj_hr_work_shift
|  |  `- aj_workshift_overtime
|  |     `- aj_hr_overtime
|  `- aj_hr_overtime
+- bemo_overtime_project
+- bemo_overtime_holiday
`- bemo_api_overtime
   `- bemo_api_overtime_project
```

Nhanh API cho SCG/AJ:

```text
scg_hr_overtime -> scg_rest_api -> scg_api_overtime
scg_rest_api + aj_workshift_overtime -> aj_rest_api -> aj_api_hr_work_shift
```

## 4) Cac module Overtime chinh

### 4.1 `bemo_hr_overtime` (core office overtime)

- Manifest: `bemo_addons/bemo_hr_overtime/__manifest__.py`
- Vai tro:
  - Module nen tang cho OT van phong
  - Tao root menu `Overtime`
  - Quan ly request, type, luong approve co ban
- Model chinh:
  - `hr.overtime`
  - `hr.overtime.type`
  - Ke thua `hr.employee`, `res.company`

### 4.2 `scg_hr_overtime` (layer SCG)

- Manifest: `scg_addons/scg_hr_overtime/__manifest__.py`
- Phu thuoc:
  - `bemo_hr_overtime`
- Vai tro:
  - Ke thua OT core cho quy trinh SCG
  - Bo sung `hr.overtime.line` (tach dong OT chi tiet)
  - Bo sung import OT
  - Bo sung reporting OT theo dong va theo thang
  - Bo sung wizard tu choi (`hr.overtime.refuse.wizard`)
- Menu bo sung:
  - `Reporting`
  - `Import`

### 4.3 `bemo_overtime_project` (OT theo project)

- Manifest: `bemo_addons/bemo_overtime_project/__manifest__.py`
- Phu thuoc:
  - `bemo_project`
  - `bemo_hr_overtime`
  - `bemo_hr_contract`
- Vai tro:
  - Mo rong OT de approve theo project manager
  - Co report phan tich OT theo project

### 4.4 `bemo_overtime_holiday` (OT ngay le)

- Manifest: `bemo_addons/bemo_overtime_holiday/__manifest__.py`
- Phu thuoc:
  - `bemo_project`
  - `bemo_time_off`
- Vai tro:
  - Mo rong rule/type OT cho truong hop holiday

### 4.5 `aj_workshift_overtime` (OT theo ca lam)

- Manifest: `aj_addons/aj_workshift_overtime/__manifest__.py`
- Phu thuoc:
  - `aj_hr_work_shift`
  - `scg_time_off`
  - `queue_job`
- Vai tro:
  - Nhanh OT cho `Overtime for Shift`
  - Co booking OT theo ca va duyet theo ca
  - Dong bo voi payroll qua model payslip ot line
- Model chinh:
  - `hr.ws.overtime`
  - `hr.ws.overtime.type`
  - `hr.ws.overtime.booking`
  - `hr.overtime.shift`
  - `hr.overtime.shift.line`

### 4.6 `aj_hr_overtime` (bao cao/export OT cho AJ)

- Manifest: `aj_addons/aj_hr_overtime/__manifest__.py`
- Phu thuoc:
  - `bemo_hr_overtime`
  - `scg_hr_overtime`
  - `aj_workshift_overtime`
- Vai tro:
  - Bo sung report tong hop OT thang:
    - `report.hr.overtime.monthly`
  - Bo sung wizard export:
    - `ot.export.wizard`
  - Them menu report OT thang

## 5) Cac module lien quan gian tiep den Overtime

### 5.1 Nhom API

- `bemo_api_overtime`
  - API cho `hr.overtime`, `hr.overtime.type`
- `bemo_api_overtime_project`
  - API cho OT + project
- `scg_rest_api`
  - Schema cho `hr_overtime.xml`, `hr_overtime_line.xml`
- `scg_api_overtime`
  - Controller/model API bo sung cho OT SCG
- `aj_rest_api`
  - Schema cho `hr_overtime`, `hr_overtime_line`, `hr_ws_overtime`, `hr_ws_overtime_booking`
- `aj_api_hr_work_shift`
  - API layer cho nhanh workshift + OT shift

### 5.2 Nhom Payroll

- `bemo_payroll`
  - Depends `bemo_hr_overtime`
- `scg_payroll`
  - Depends `scg_hr_overtime`
  - Co view lien quan OT trong payroll flow

### 5.3 Nhom Dashboard

- `scg_system_dashboard`
  - Depends `scg_hr_overtime`
  - Co nhieu chart OT (OT amount/hours/rate/by department)
- `aj_system_dashboard`
  - Ke thua `scg_system_dashboard`
  - Co chart OT bo sung cho AJ

### 5.4 Nhom Notification (FCM)

- `scg_fcm`
  - Cau hinh FCM cho `hr_overtime`, `hr_overtime_line`
- `aj_fcm`
  - Cau hinh FCM cho nhanh `aj_workshift_overtime`

### 5.5 Nhom Attendance tong hop

- `bemo_attendane_summary`
  - Depends `bemo_hr_overtime`
  - Tong hop attendance/timeoff/overtime theo thang

## 6) Goi y stack theo boi canh

- Base Office OT:
  - `bemo_hr_overtime`
  - + `bemo_overtime_project` (neu can OT theo project)
  - + `bemo_overtime_holiday` (neu can rule holiday)

- Stack SCG:
  - `bemo_hr_overtime` + `scg_hr_overtime`
  - + `scg_rest_api` / `scg_api_overtime` (neu can mobile/API)

- Stack AJ day du (Office + Shift):
  - Stack SCG
  - + `aj_hr_work_shift` + `aj_workshift_overtime`
  - + `aj_hr_overtime`
  - + `aj_rest_api` / `aj_api_hr_work_shift` (neu can API)

