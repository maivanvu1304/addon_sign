/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// Colors for signers
const SIGNER_COLORS = [
    '#e91e8c', '#2196f3', '#4caf50', '#ff9800',
    '#9c27b0', '#00bcd4', '#f44336', '#795548',
];

class SignDocumentEditor extends Component {
    static template = "ds_sign.SignDocumentEditor";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.pdfContainerRef = useRef("pdfContainer");
        this.canvasRef = useRef("pdfCanvas");

        this.state = useState({
            documentId: this.props.action.context.document_id,
            signers: [],
            currentPage: 1,
            totalPages: 1,
            pdfScale: 1.5,
            pdfUrl: null,
            attachmentId: null,
            loading: true,
            hasSigned: false,
        });

        onMounted(() => this._init());
    }

    async _init() {
        const docId = this.state.documentId;
        const [doc] = await this.orm.read('ds.document', [docId], [
            'name', 'title', 'attachment_id', 'request_item_ids',
        ]);

        const items = await this.orm.read('ds.document.request.item', doc.request_item_ids, [
            'id', 'user_id', 'role', 'state',
            'signature_pos_x', 'signature_pos_y', 'page_number', 'name', 'is_current_user',
        ]);

        const signers = items.map((item, idx) => ({
            item_id: item.id,
            name: item.user_id ? item.user_id[1] : (item.name || `Người ký ${idx + 1}`),
            role: item.role || 'sign',
            state: item.state,
            color: SIGNER_COLORS[idx % SIGNER_COLORS.length],
            page: item.page_number || 1,
            x: item.signature_pos_x || 0,
            y: item.signature_pos_y || 0,
            placed: !!(item.signature_pos_x || item.signature_pos_y),
            is_current_user: item.is_current_user,
            signedName: '', // Holds the name they typed
            signing: false, // Whether they are currently typing their name
        }));

        this.state.signers = signers;

        if (doc.attachment_id && doc.attachment_id.length > 0) {
            const attachId = Array.isArray(doc.attachment_id[0])
                ? doc.attachment_id[0][0]
                : doc.attachment_id[0];
            this.state.attachmentId = attachId;
            this.state.pdfUrl = `/web/content/${attachId}?download=false`;
        }

        this.state.loading = false;
        await this._loadPdf();
    }

    async _loadPdf() {
        if (!this.state.pdfUrl) return;

        if (!window.pdfjsLib) {
            await this._loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js');
            window.pdfjsLib.GlobalWorkerOptions.workerSrc =
                'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }

        this.pdfDoc = await window.pdfjsLib.getDocument(this.state.pdfUrl).promise;
        this.state.totalPages = this.pdfDoc.numPages;
        await this._renderPage(this.state.currentPage);
    }

    async _renderPage(pageNum) {
        if (!this.pdfDoc) return;
        const page = await this.pdfDoc.getPage(pageNum);
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const viewport = page.getViewport({ scale: this.state.pdfScale });
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const ctx = canvas.getContext('2d');
        await page.render({ canvasContext: ctx, viewport }).promise;
    }

    async _loadScript(src) {
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
        });
    }

    async prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            await this._renderPage(this.state.currentPage);
        }
    }

    async nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
            await this._renderPage(this.state.currentPage);
        }
    }

    onClickSignBox(signer) {
        if (signer.state === 'pending' && signer.is_current_user) {
            signer.signing = true;
        } else if (signer.state === 'pending' && !signer.is_current_user) {
            this.notification.add("Đây không phải là vị trí ký của bạn.", { type: "danger" });
        }
    }

    onSignNameInput(ev, signer) {
        signer.signedName = ev.target.value;
    }

    onSignNameEnter(ev, signer) {
        if (ev.key === 'Enter') {
            this.confirmSignature(signer);
        }
    }

    confirmSignature(signer) {
        if (!signer.signedName.trim()) {
            this.notification.add("Vui lòng nhập tên của bạn.", { type: "warning" });
            return;
        }
        signer.signing = false;
        signer.state = 'done_local'; // Temp state before saving to backend
        this.state.hasSigned = true;
    }

    async submitSignature() {
        const signedItem = this.state.signers.find(s => s.state === 'done_local');
        if (!signedItem) {
            this.notification.add("Không có chữ ký nào mới để gửi.", { type: "warning" });
            return;
        }

        // Call action_approve on this item
        await this.orm.call('ds.document.request.item', 'action_approve', [[signedItem.item_id]]);

        // Cập nhật note thành tên người dùng đã ký
        await this.orm.write('ds.document.request.item', [signedItem.item_id], {
            note: "Đã ký bằng tên: " + signedItem.signedName,
        });

        this.notification.add("Ký thành công!", { type: "success" });
        this.backToDocument();
    }

    backToDocument() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'ds.document',
            res_id: this.state.documentId,
            views: [[false, 'form']],
            target: 'current',
        });
    }
}

SignDocumentEditor.template = "ds_sign.SignDocumentEditor";

registry.category("actions").add("ds_sign_document", SignDocumentEditor);
