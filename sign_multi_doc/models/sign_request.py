from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64


class SignRequest(models.Model):
    _inherit = 'sign.request'
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Additional Documents to Sign",
        help="Upload extra PDF documents that should be included in this signature request (envelope)."
    )
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._post_process_attachments()
        return records
    def write(self, vals):
        res = super().write(vals)
        if 'attachment_ids' in vals:
            for rec in self:
                rec._post_process_attachments()
        return res

    def _post_process_attachments(self):
        """Create sign.request.document for each attachment if not already linked."""
        self.ensure_one()
        existing_docs = self.env['sign.request.document'].search([('sign_request_id', '=', self.id)])
        existing_attachment_ids = set(existing_docs.mapped('attachment_id.id'))

        for attachment in self.attachment_ids:
            if attachment.id in existing_attachment_ids:
                continue
            if not attachment.datas:
                continue

            self.env['sign.request.document'].create({
                'name': attachment.name,
                'datas': attachment.datas,
                'mimetype': attachment.mimetype,
                'attachment_id': attachment.id,
                'sign_request_id': self.id,
            })

    def action_send_multiple_documents(self):
        for rec in self:
            if rec.attachment_ids:
                rec._post_process_attachments()

    def action_send(self):
        self.action_send_multiple_documents()
        return super().action_send()
