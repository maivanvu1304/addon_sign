# Module Specification: `sign_dochub`

> Tài liệu này được viết lại theo code hiện tại trong `custom_addons/sign_dochub` (không mô tả theo bản thiết kế cũ).

## 1. Metadata

| Thuộc tính | Giá trị |
|---|---|
| Technical name | `sign_dochub` |
| Version | `19.0.1.0.0` |
| Category | `Document Management` |
| License | `LGPL-3` |
| Depends | `base`, `hr`, `mail`, `portal` |
| Application | `True` |

## 2. Mục tiêu và phạm vi thực tế

Module cung cấp luồng trình ký tuần tự nhiều bước trên chứng từ nội bộ:

- Quản lý chứng từ và tệp PDF đính kèm.
- Thiết lập danh sách bước ký/phê duyệt (`ds.document.request.item`).
- Đặt vị trí ký trên PDF bằng giao diện kéo thả (client action).
- Ký trực tiếp bằng tên nhập tay, sau đó ghi chữ ký text vào PDF.
- Gửi email thông báo theo từng bước nội bộ.
- Ban hành kết quả cho khách hàng qua portal token đơn giản.

Phạm vi chưa có hoặc mới ở mức placeholder:

- `action_share()` chưa có logic.
- `action_preview()` của khách hàng chưa có logic.
- Menu “Ký hàng loạt / Duyệt hàng loạt” chưa có wizard riêng.
- Model `ds.sign.log` chưa có trong module nhưng đang được gọi ở nút lịch sử ký.
- `ds.sign.position.wizard` có file model nhưng chưa được import vào `models/__init__.py`.

## 3. Kiến trúc chức năng

### 3.1 Models chính

- `ds.document`: chứng từ trung tâm, quản lý trạng thái và workflow.
- `ds.document.request.item`: từng bước xử lý (ký hoặc phê duyệt).
- `ds.document.customer`: danh sách khách hàng nhận thông báo sau khi hoàn tất.
- `ds.document.template` + `ds.document.template.step`: mẫu luồng xử lý.
- `ds.document.type`: loại chứng từ, có liên kết default template.

### 3.2 Controller portal

- `controllers/controllers.py` định nghĩa route xem/tải chứng từ cho khách hàng bằng `verification_code`.

### 3.3 Frontend (OWL + PDF.js)

- Client action `ds_sign_position_editor`: kéo thả vị trí ký.
- Client action `ds_sign_document`: ký bằng nhập tên tại vị trí đã đặt.
- View widget `ds_pdf_preview`: panel xem trước vị trí ký trong trạng thái `adjusting`.

## 4. Workflow thực tế của `ds.document`

## 4.1 Trạng thái chứng từ

- `draft`
- `in_progress`
- `adjusting`
- `done`
- `rejected`
- `cancelled`

## 4.2 Luồng xử lý

1. Tạo chứng từ ở `draft`, khai báo các bước trong `request_item_ids`.
2. Bấm `action_start_workflow`:
   - Validate phải có ít nhất 1 bước.
   - Chuyển `state = in_progress`.
   - Ghi `date_request`.
3. Bấm `action_adjust`:
   - Chuyển `state = adjusting`.
   - Reset `position_confirmed = False`.
4. Trong `adjusting`, người dùng mở `action_open_sign_position` để đặt tọa độ ký cho từng bước role `sign`.
5. Bấm `action_confirm_positions` (nút “Gửi quy trình”):
   - Bắt buộc có bước ký.
   - Bắt buộc mọi bước `role != approve` có tọa độ (`x` hoặc `y` khác 0).
   - Set `position_confirmed = True`.
   - Nếu chưa có bước nào bắt đầu thì gọi `_activate_next_step()` để đưa bước đầu tiên sang `pending`.
6. Khi bước hiện tại là `sign`:
   - `action_send_sign_request` mở client action `ds_sign_document`.
   - Người ký nhập tên, JS ghi vào `note` dạng prefix: `Đã ký bằng tên: ...`.
   - Quay lại form, bấm `action_finish_sign_step`:
     - Validate bước pending đã ký (dựa vào `note`).
     - `action_approve()` bước đó -> `done`.
     - Nếu có tọa độ thì ghi chữ ký text vào PDF (`_burn_signature_to_pdf`).
     - Gọi `_activate_next_step()`.
7. Khi bước hiện tại là `approve`:
   - Bấm `action_approve_step`.
   - Bước pending chuyển `done`.
   - Gọi `_activate_next_step()`.
8. Từ chối:
   - `action_reject_document` chuyển chứng từ `rejected`.
   - Các bước chưa hoàn tất chuyển `rejected`.
9. Yêu cầu ký lại:
   - `action_request_resign` reset từ bước ngay trước bước pending trở đi về `draft`.
   - Xóa `date_action`, `date_sent`, `note`.
   - Gọi lại `_activate_next_step()` để chạy lại tuần tự.
10. Hoàn tất:
   - `_activate_next_step()` không còn draft step -> `_check_workflow_complete()`.
   - Nếu tất cả bước `done`, chứng từ `done` và set `date_done`.

## 4.3 Trạng thái `ds.document.request.item`

- `draft` -> `pending` -> `done`
- Có thể chuyển sang `rejected` hoặc `cancelled` tùy action trên chứng từ.

## 5. Chi tiết data model

## 5.1 `ds.document`

Kế thừa:

- `mail.thread`
- `mail.activity.mixin`
- `portal.mixin`

Field quan trọng:

- Thông tin chứng từ: `name`, `title`, `description`, `document_type_id`, `department_id`, `related_document_id`, `coordinator_id`, `viewer_ids`.
- Tệp: `attachment_id` (Many2many, required), `signed_attachment_id`, `related_attachment_ids`, `password`.
- Cấu hình hiển thị ký: `auto_sign_position`, `render_mode`.
- Khách hàng/thời gian: `partner_id`, `contract_value`, `currency_id`, `date_deadline`, `date_effective_from`, `date_effective_to`.
- Workflow: `state`, `position_confirmed`, `template_id`, `request_item_ids`, `customer_ids`, `date_request`, `date_done`.
- Huỷ: `cancel_reason`, `cancel_user_id`, `cancel_date`.
- Computed: `current_signer_id`, `current_signer_state`, `current_signer_role`, `item_count`, `item_done_count`, `attachment_count`, `sign_history_count`, `sign_positions_set`, `can_finish_sign_step`, `can_request_resign`.

Lưu ý kỹ thuật:

- `name` auto-sequence theo `ir.sequence` code `ds.document` (`DS-00001`...).
- `attachment_count` chỉ đếm khi state khác `draft`.
- `sign_history_count` đang đếm `mail.message` dạng `notification`, không phải bảng log ký chuyên biệt.

## 5.2 `ds.document.request.item`

Field chính:

- Liên kết: `document_id`, `sequence`, `role`, `user_id`, `partner_id`.
- Liên hệ: `email`, `phone`.
- Trạng thái: `state`, `date_sent`, `date_action`, `note`.
- Token: `access_token` (uuid mặc định).
- Ký PDF: `signature_pos_x`, `signature_pos_y`, `page_number`.
- Theo user hiện tại: `is_current_user` (compute theo `uid`).

Method đáng chú ý:

- `action_approve()`:
  - Set `state = done`, `date_action`.
  - Nếu role là ký và có tọa độ thì gọi `_burn_signature_to_pdf()`.
- `_burn_signature_to_pdf()`:
  - Dùng `PyPDF2` + `reportlab`.
  - Nguồn PDF: `signed_attachment_id` nếu có, nếu không lấy `attachment_id[0]`.
  - Ghi tên người ký + timestamp vào trang PDF đã chọn.
  - Cập nhật/tạo `signed_attachment_id`.
- `_send_notification_email()`:
  - Gửi mail thủ công qua `mail.mail` (không dùng `mail.template`).
  - Link trong mail nội bộ trỏ về backend form (`/web#id=...&model=ds.document&view_type=form`).

## 5.3 `ds.document.customer`

Field chính:

- `document_id`, `partner_id`, `email`, `phone`.
- `verification_code` (6 ký tự ngẫu nhiên chữ + số).
- `is_sent`, `date_sent`.

Method chính:

- `_generate_code()`: sinh mã xác thực.
- `_onchange_partner_id()`: copy email từ partner.
- `action_send_customer_email()`:
  - Gửi email ban hành có link portal: `/my/documents/<id>?access_token=<verification_code>`.
  - Đính kèm `signed_attachment_id` nếu có, nếu không đính file gốc.
  - Cập nhật cờ đã gửi và ghi chatter.
- `action_preview()`: placeholder.

## 5.4 `ds.document.template` / `ds.document.template.step`

- Quản lý mẫu quy trình và các bước (`sequence`, `name`, `role`, `user_id`, `is_external`, `partner_id`).
- `ds.document.apply_template()`:
  - Xóa các item đang `draft`.
  - Tạo item mới từ template step.
- `ds.document.save_as_template()`:
  - Tạo template mới từ item hiện tại.
  - Hiện chỉ lưu `user_id` cho step, chưa lưu `partner_id`.

## 5.5 `ds.document.type`

- `name`, `code`, `sequence_id`, `default_template_id`.
- Hiện chưa có logic tự động áp dụng `default_template_id` khi chọn loại chứng từ.

## 6. Views và hành vi UI

## 6.1 Form `ds.document`

Header button theo state:

- `draft`: `action_start_workflow`.
- `in_progress`: `action_adjust`, `action_cancel`.
- `adjusting` (trước khi chốt vị trí): `action_open_sign_position`, `action_reset_positions`, `action_confirm_positions`.
- `adjusting` (sau khi chốt vị trí):
  - Nếu bước hiện tại là ký: `action_send_sign_request`, `action_finish_sign_step`.
  - Nếu bước hiện tại là duyệt: `action_approve_step`.
  - Luôn có `action_reject_document`.
  - Có thể `action_request_resign` nếu đủ điều kiện.
- `done`: `action_publish`, `action_cancel`.
- `rejected`/`cancelled`: `action_reset_to_draft`.

Bố cục:

- `state = adjusting` dùng layout chuyên biệt + widget `ds_pdf_preview` trong vùng chatter.
- Các state khác dùng form đầy đủ (tabs thông tin, quy trình nội bộ, quy trình khách hàng).
- Tab “Quy trình khách hàng” chỉ hiện khi `state = done`.

## 6.2 List/Search/Actions

- List view có badge/decoration theo state.
- Action chính:
  - `ds_document_action` (Documents).
  - `ds_document_file_list_action` lọc state `in_progress` và `adjusting`.

## 6.3 Attachments view

- Nút stat “Files” mở action `ds_attachment_action` trên `ir.attachment` dạng `kanban,list`.

## 7. Portal và public routes

Định nghĩa trong `controllers/controllers.py`:

1. `GET /my/documents/<document_id>?access_token=<verification_code>`
   - `auth='public'`, `website=True`.
   - Validate bằng bảng `ds.document.customer`.
   - Render `sign_dochub.ds_document_portal_template`.
2. `GET /my/documents/<document_id>/download?access_token=<verification_code>&download=true|false`
   - `auth='public'`.
   - Validate token tương tự.
   - Trả stream file (`signed_attachment_id` ưu tiên, nếu không lấy file gốc đầu tiên).

Lưu ý:

- Token đang dùng `verification_code` khách hàng, không dùng token chuẩn của `portal.mixin`.
- Portal template hiển thị badge “Đã hoàn tất” cố định.

## 8. Security

## 8.1 Groups

- `group_ds_user` (implied `base.group_user`).
- `group_ds_manager` (implied `group_ds_user`).

## 8.2 ACL (`ir.model.access.csv`)

- `ds.document`, `ds.document.request.item`, `ds.document.customer`: user có read/write/create, manager có full quyền.
- `ds.document.type`, `ds.document.template`, `ds.document.template.step`: user chỉ read, manager full quyền.

## 8.3 Record rules

- User chỉ thấy chứng từ liên quan qua:
  - `creator_id`
  - `coordinator_id`
  - `viewer_ids`
  - `request_item_ids.user_id`
- Manager có rule “see all”.

## 9. Data, assets, menu

Data nạp:

- `security/security.xml`
- `security/ir.model.access.csv`
- `data/sequence_data.xml`
- `views/*.xml` (document/type/template/menu/attachment/portal)

Assets backend:

- JS/XML/SCSS cho:
  - `sign_position_editor`
  - `sign_document`
  - `ds_pdf_preview`

Menu:

- Root `Dochub`
- `Chứng từ`
- `Danh sách file ký`
- `Ký hàng loạt` (placeholder)
- `Duyệt hàng loạt` (placeholder)
- `Cấu hình` -> `Mẫu quy trình`, `Loại chứng từ`

## 10. Khoảng trống và rủi ro kỹ thuật hiện tại

1. `ds.sign.log` chưa tồn tại nhưng đang dùng trong `action_view_sign_history`.
2. `ds_sign_position_wizard.py` chưa được import, nên model wizard không có hiệu lực.
3. Hành vi ký PDF chỉ áp dụng cho `attachment_id[0]` (file đầu tiên), chưa xử lý đa file đầy đủ.
4. Email nội bộ và email khách hàng hard-code HTML trong Python, chưa chuẩn hóa bằng `mail.template`.
5. Trường `is_external` trong template step chưa có luồng nghiệp vụ thực tế đi kèm.
6. `action_cancel` chưa ghi lý do huỷ dù có các field `cancel_reason`, `cancel_user_id`, `cancel_date`.
7. Chưa có test tự động trong module.

## 11. Test scenario tối thiểu đề xuất (UAT)

1. Tạo chứng từ mới, thêm 2 bước (ký -> duyệt), chạy full flow đến `done`.
2. Kiểm tra role `approve` không cần vị trí ký và vẫn đi tiếp đúng.
3. Ký bằng tên, xác nhận file `signed_attachment_id` được tạo/cập nhật.
4. Từ chối ở bước pending, kiểm tra trạng thái chứng từ và item.
5. Yêu cầu ký lại ở bước duyệt, kiểm tra reset đúng từ bước trước đó.
6. Ban hành cho khách hàng, kiểm tra email gửi và portal link truy cập được bằng `verification_code`.
