# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from io import StringIO

import os.path
import xhtml2pdf.pisa as pisa


DATA_PATH = os.environ['BUILDOUT_DIR']
DOSSIER_STRUCTURE_PATH = os.path.join(DATA_PATH, 'var/dossier-structure')
if not os.path.exists(DOSSIER_STRUCTURE_PATH):
    os.mkdir(DOSSIER_STRUCTURE_PATH)


def _get_pdf_file_path(ds):
    """ """
    DS_PDFFILE_NAME = ds.id + '.pdf'
    DS_PDFFILE_PATH = os.path.join(DOSSIER_STRUCTURE_PATH, DS_PDFFILE_NAME)
    return DS_PDFFILE_PATH


def pdf(self):
    """
      returns a pdf file for a Dossier Structuré
      can be called on any DosierStructure content type
    """
    member = self.portal_membership.getAuthenticatedMember()
    # if enough credit, return pdf file
    # member can not be Free, must have enough credits and credits can not be 0
    if not member.is_cedes_free() and \
       member.check_balance(self.get_price()) and \
       member.get_balance():
        member.add_transaction(self.UID(), self.get_price(), id_dossier_structure=True)
        # remember access to sub ArticlePayant
        all_ressource_uids = self.get_all_ressource_uids()
        already_payed_uids = [elt[0] for elt in member.get_transactions()]
        for paying in self.get_paying_ressources(all_ressource_uids):
            # as already payed here above by the DossierStructure price
            # just remember the access to the ArticlePayant but with a price of 0
            paying_uid = paying.UID
            if paying_uid not in already_payed_uids:
                member.add_transaction(paying_uid, 0)
        pdffile_path = _get_pdf_file_path(self)
        pdf_file = open(pdffile_path, "rb")
        self.REQUEST.RESPONSE.setHeader('Content-Type', 'application/pdf')
        self.REQUEST.RESPONSE.setHeader('Content-Disposition', 'attachment; filename=%s' % self.id + '.pdf')
        pdf_data = pdf_file.read()
        pdf_file.close()
        return pdf_data
    # else retrun not enough credit.
    self.plone_utils.addPortalMessage("SOLDE INSUFFISANT", type='error')
    return self.REQUEST.RESPONSE.redirect(self.absolute_url())


def generate_pdf(self):
    """
      genrerates a pdf file for the Dossier Structuré
      Pdf files are stored in the var/dossier-structure directory on the server
      can be called on any DosierStructure content type
    """

    DS_PDFFILE_NAME = self.id + '.pdf'
    DS_PDFFILE_PATH = os.path.join(DOSSIER_STRUCTURE_PATH, DS_PDFFILE_NAME)

    pdf_file = open(DS_PDFFILE_PATH, "wb")

    content = self.restrictedTraverse('@@dossierstructure_pdf')()

    pisa.CreatePDF(
          StringIO(content),
          pdf_file,
          link_callback=pisa.pisaLinkLoader(content).getFileName
          )
    pdf_file.close()
    self.plone_utils.addPortalMessage('PDF généré.')
    return self.REQUEST.RESPONSE.redirect(self.absolute_url())


def pdf_libre(self):
    """
      returns a pdf file for a "Formation"
      can be called on any Training content type
    """

    pdf_file = StringIO()

    # xhtml2pdf does not support unicode...
    content = self.formation_pdf(network="Libre").encode('utf-8')

    pisa.CreatePDF(
          StringIO(content),
          pdf_file,
          link_callback=pisa.pisaLinkLoader(content).getFileName
          )

    self.REQUEST.RESPONSE.setHeader('Content-Type', 'application/pdf')
    self.REQUEST.RESPONSE.setHeader('Content-Disposition', 'attachment; filename=%s' % self.id + '-libre.pdf')
    return pdf_file.getvalue()


def pdf_officiel(self):
    """
      returns a pdf file for a "Formation""
      can be called on any Training content type
    """

    pdf_file = StringIO()

    content = self.formation_pdf(network="Officiel").encode('utf-8')

    pisa.CreatePDF(
          StringIO(content),
          pdf_file,
          link_callback=pisa.pisaLinkLoader(content).getFileName
          )

    self.REQUEST.RESPONSE.setHeader('Content-Type', 'application/pdf')
    self.REQUEST.RESPONSE.setHeader('Content-Disposition', 'attachment; filename=%s' % self.id + '-officiel.pdf')
    return pdf_file.getvalue()
