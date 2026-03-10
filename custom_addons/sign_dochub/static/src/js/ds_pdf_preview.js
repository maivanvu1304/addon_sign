/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted, onWillUpdateProps, useRef, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


// Màu cho từng signer
const SIGNER_COLORS = [
    '#e91e8c', '#2196f3', '#4caf50', '#ff9800',
    '#9c27b0', '#00bcd4', '#f44336', '#795548',
];

// ============================================================
// PDF Preview Panel Widget
// ============================================================
export class DsPdfPreviewPanel extends Component {
    static template = "ds_sign.DsPdfPreviewPanel";
    static components = {};
    static props = ["*"];  // Accept all props from view_widgets registry

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.canvasRef = useRef("pdfCanvas");
        this.containerRef = useRef("pdfContainer");

        this.state = useState({
            signers: [],
            currentPage: 1,
            totalPages: 1,
            pdfUrl: null,
            loading: false,
        });

        // Reload khi record thay đổi
        useEffect(
            () => {
                const rec = this.props.record;
                console.log('[DsPdfPreview] useEffect triggered, record:', rec);
                if (rec) {
                    const state = rec.data ? rec.data.state : null;
                    console.log('[DsPdfPreview] document state:', state);
                    if (state === 'adjusting') {
                        this._loadData();
                    }
                }
            },
            () => {
                const rec = this.props.record;
                if (rec && rec.data) {
                    return [rec.data.state, rec.resId || rec.data.id];
                }
                return [];
            }
        );
    }

    get isAdjusting() {
        const rec = this.props.record;
        return rec && rec.data && rec.data.state === 'adjusting';
    }

    get recordId() {
        const rec = this.props.record;
        return rec.resId || (rec.data && rec.data.id);
    }

    // ==================== Load Data ====================

    async _loadData() {
        this.state.loading = true;
        const docId = this.recordId;
        console.log('[DsPdfPreview] _loadData started, docId:', docId);

        if (!docId) {
            console.warn('[DsPdfPreview] No document ID found');
            this.state.loading = false;
            return;
        }

        try {
            // Load attachment_id (Many2many) via ORM — most reliable approach
            const [doc] = await this.orm.read('ds.document', [docId], ['attachment_id']);
            console.log('[DsPdfPreview] ORM read attachment_id result:', doc);

            if (doc.attachment_id && doc.attachment_id.length > 0) {
                // Many2many field: orm.read returns array of IDs [1, 2, 3]
                const attachId = doc.attachment_id[0];
                this.state.pdfUrl = `/web/content/${attachId}?download=false`;
                console.log('[DsPdfPreview] PDF URL set:', this.state.pdfUrl);
            } else {
                console.warn('[DsPdfPreview] No attachments found for document', docId);
            }

            // Load request items (signers)
            const [doc2] = await this.orm.read('ds.document', [docId], ['request_item_ids']);
            console.log('[DsPdfPreview] request_item_ids:', doc2.request_item_ids);

            if (doc2.request_item_ids && doc2.request_item_ids.length > 0) {
                const items = await this.orm.read(
                    'ds.document.request.item',
                    doc2.request_item_ids,
                    ['id', 'user_id', 'role', 'state', 'signature_pos_x', 'signature_pos_y', 'page_number', 'name']
                );
                console.log('[DsPdfPreview] Loaded signers:', items);

                this.state.signers = items.map((item, idx) => ({
                    item_id: item.id,
                    name: item.user_id ? item.user_id[1] : (item.name || `Người ký ${idx + 1}`),
                    role: item.role || 'sign',
                    itemState: item.state,
                    color: SIGNER_COLORS[idx % SIGNER_COLORS.length],
                    page: item.page_number || 1,
                    x: item.signature_pos_x || 0,
                    y: item.signature_pos_y || 0,
                    placed: !!(item.signature_pos_x || item.signature_pos_y),
                }));
            }

            this.state.loading = false;
            await this._loadPdf();
        } catch (e) {
            console.error('[DsPdfPreview] Load error:', e);
            this.state.loading = false;
        }
    }

    // ==================== PDF.js ====================

    async _loadPdf() {
        if (!this.state.pdfUrl) return;

        if (!window.pdfjsLib) {
            await this._loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js');
            window.pdfjsLib.GlobalWorkerOptions.workerSrc =
                'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }

        try {
            this.pdfDoc = await window.pdfjsLib.getDocument(this.state.pdfUrl).promise;
            this.state.totalPages = this.pdfDoc.numPages;
            await this._renderPage(this.state.currentPage);
        } catch (e) {
            console.error('PDF load error:', e);
        }
    }

    async _renderPage(pageNum) {
        if (!this.pdfDoc) return;
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const page = await this.pdfDoc.getPage(pageNum);
        const container = this.containerRef.el;
        const containerWidth = container ? container.offsetWidth - 4 : 600;
        const unscaledViewport = page.getViewport({ scale: 1 });
        const scale = containerWidth / unscaledViewport.width;
        const viewport = page.getViewport({ scale });

        canvas.width = viewport.width;
        canvas.height = viewport.height;
        this.currentScale = scale;

        const ctx = canvas.getContext('2d');
        await page.render({ canvasContext: ctx, viewport }).promise;
    }

    _loadScript(src) {
        return new Promise((resolve, reject) => {
            if (document.querySelector(`script[src="${src}"]`)) return resolve();
            const s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
        });
    }

    // ==================== Navigation ====================

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

    signerStateLabel(st) {
        const map = { draft: 'Nhập', pending: 'Đang chờ', done: 'Đã ký', rejected: 'Từ chối', cancelled: 'Đã hủy' };
        return map[st] || st;
    }
}

// Register as form view widget
registry.category("view_widgets").add("ds_pdf_preview", {
    component: DsPdfPreviewPanel,
});
