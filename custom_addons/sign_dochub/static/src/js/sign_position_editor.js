/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// Màu sắc cho từng người ký
const SIGNER_COLORS = [
    '#e91e8c', '#2196f3', '#4caf50', '#ff9800',
    '#9c27b0', '#00bcd4', '#f44336', '#795548',
];

class SignPositionEditor extends Component {
    static template = "ds_sign.SignPositionEditor";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.pdfContainerRef = useRef("pdfContainer");
        this.canvasRef = useRef("pdfCanvas");

        this.state = useState({
            documentId: this.props.action.context.document_id,
            signers: [],          // [{id, name, color, role, items: [{item_id, page, x, y}]}]
            currentPage: 1,
            totalPages: 1,
            pdfScale: 1.5,
            selectedSignerIndex: null,
            dragging: null,       // {signerIdx, itemIdx}
            pdfUrl: null,
            attachmentId: null,
            loading: true,
        });

        onMounted(() => this._init());
    }

    async _init() {
        const docId = this.state.documentId;
        // Load document + request items
        const [doc] = await this.orm.read('ds.document', [docId], [
            'name', 'title', 'attachment_id', 'request_item_ids',
        ]);

        // Load request items
        const items = await this.orm.read('ds.document.request.item', doc.request_item_ids, [
            'id', 'user_id', 'role', 'state',
            'signature_pos_x', 'signature_pos_y', 'page_number', 'name',
        ]);

        // Build signers list
        const signers = items.map((item, idx) => ({
            item_id: item.id,
            name: item.user_id ? item.user_id[1] : (item.name || `Người ký ${idx + 1}`),
            role: item.role || 'sign',
            state: item.state,
            color: SIGNER_COLORS[idx % SIGNER_COLORS.length],
            requiresPosition: (item.role || 'sign') !== 'approve',
            page: (item.role || 'sign') === 'approve' ? 1 : (item.page_number || 1),
            x: (item.role || 'sign') === 'approve' ? 0 : (item.signature_pos_x || 0),
            y: (item.role || 'sign') === 'approve' ? 0 : (item.signature_pos_y || 0),
            placed: (item.role || 'sign') === 'approve' ? false : !!(item.signature_pos_x || item.signature_pos_y),
        }));

        this.state.signers = signers;

        // Get PDF attachment (first one)
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

        // Load PDF.js từ CDN nếu chưa có
        if (!window.pdfjsLib) {
            await this._loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js');
            window.pdfjsLib.GlobalWorkerOptions.workerSrc =
                'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }

        const pdf = await window.pdfjsLib.getDocument(this.state.pdfUrl).promise;
        this.pdfDoc = pdf;
        this.state.totalPages = pdf.numPages;
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

    // ===== Navigation =====

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

    // ===== Kéo thả chữ ký lên PDF =====

    onCanvasMouseDown(e) {
        // Nếu đang kéo một signer box đã tồn tại
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Check xem có click vào box nào không
        const signers = this.state.signers.filter(
            s => s.requiresPosition && s.page === this.state.currentPage && s.placed
        );
        for (let i = signers.length - 1; i >= 0; i--) {
            const s = signers[i];
            if (x >= s.x && x <= s.x + 160 && y >= s.y && y <= s.y + 60) {
                this.state.dragging = { signerIdx: this.state.signers.indexOf(s), offsetX: x - s.x, offsetY: y - s.y };
                return;
            }
        }
    }

    onCanvasMouseMove(e) {
        if (!this.state.dragging) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left - this.state.dragging.offsetX;
        const y = e.clientY - rect.top - this.state.dragging.offsetY;
        const signer = this.state.signers[this.state.dragging.signerIdx];
        signer.x = Math.max(0, x);
        signer.y = Math.max(0, y);
    }

    onCanvasMouseUp() {
        this.state.dragging = null;
    }

    // Kéo signer từ sidebar thả vào PDF
    onSignerDragStart(e, idx) {
        if (!this.state.signers[idx].requiresPosition) {
            e.preventDefault();
            return;
        }
        e.dataTransfer.setData('signerIdx', idx);
    }

    onCanvasDrop(e) {
        e.preventDefault();
        const idx = parseInt(e.dataTransfer.getData('signerIdx'));
        if (Number.isNaN(idx)) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const signer = this.state.signers[idx];
        if (!signer || !signer.requiresPosition) return;
        signer.x = x;
        signer.y = y;
        signer.page = this.state.currentPage;
        signer.placed = true;
    }

    onCanvasDragOver(e) {
        e.preventDefault();
    }

    // Xóa vị trí
    removeSignerPosition(idx) {
        const signer = this.state.signers[idx];
        if (!signer || !signer.requiresPosition) return;
        signer.placed = false;
        signer.x = 0;
        signer.y = 0;
    }

    // ===== Lưu =====

    async savePositions() {
        const docId = this.state.documentId;
        const updates = this.state.signers.map(s => ({
            item_id: s.item_id,
            x: s.requiresPosition ? s.x : 0,
            y: s.requiresPosition ? s.y : 0,
            page: s.requiresPosition ? s.page : 1,
        }));

        // Ghi từng item
        for (const u of updates) {
            await this.orm.write('ds.document.request.item', [u.item_id], {
                signature_pos_x: u.x,
                signature_pos_y: u.y,
                page_number: u.page,
            });
        }

        this.notification.add("Đã lưu vị trí chữ ký!", { type: "success" });
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

SignPositionEditor.template = "ds_sign.SignPositionEditor";

registry.category("actions").add("ds_sign_position_editor", SignPositionEditor);
