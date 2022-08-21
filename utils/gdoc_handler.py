from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


class Document:
    def __init__(self, google_api: str):
        credentials = Credentials.from_service_account_file(google_api)
        self.service = build('docs', 'v1', credentials=credentials)

    def read_paragraph_element(self, element):
        # """Returns the text in the given ParagraphElement.
        #
        #     Args:
        #         element: a ParagraphElement from a Google Doc.
        # """
        text_run = element.get('textRun')
        if not text_run:
            return ''
        return text_run.get('content')

    def read_strucutural_elements(self, elements):
        # """Recurses through a list of Structural Elements to read a document's text where text may be
        #     in nested elements.
        #
        #     Args:
        #         elements: a list of Structural Elements.
        # """
        text = ''
        for value in elements:
            if 'paragraph' in value:
                elements = value.get('paragraph').get('elements')
                for elem in elements:
                    text += self.read_paragraph_element(elem)
            elif 'table' in value:
                # The text in table cells are in nested Structural Elements and tables may be
                # nested.
                table = value.get('table')
                for row in table.get('tableRows'):
                    cells = row.get('tableCells')
                    for cell in cells:
                        text += self.read_strucutural_elements(cell.get('content'))
            elif 'tableOfContents' in value:
                # The text in the TOC is also in a Structural Element.
                toc = value.get('tableOfContents')
                text += self.read_strucutural_elements(toc.get('content'))
        return text

    def read_gdoc(self, url: str):
        if url.startswith('http'):
            start = url.find("document/d/") + len("document/d/")
            end = url.find("/edit")
            if end == -1:
                return None
            url = url[start:end]
        doc = self.service.documents().get(documentId=url).execute()
        content = doc.get('body').get('content')
        return self.read_strucutural_elements(content)
