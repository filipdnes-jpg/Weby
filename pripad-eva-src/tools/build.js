const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, LevelFormat, AlignmentType, BorderStyle } = require('docx');

const lines = fs.readFileSync(process.argv[2], 'utf8').split('\n').filter(Boolean);
const colors = { 'NIKOL': '1F4E79', 'NIKOL (v duchu)': '5B7FA6', 'EVA': '8B1E3F', 'BABKA': '5A4A2F' };
const kids = [];
for (const l of lines) {
  const [t, a, b] = l.split('|');
  if (t === 'T') kids.push(new Paragraph({ heading: 'Title', children: [new TextRun(a)] }));
  else if (t === 'N') kids.push(new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: a, color: '555555', size: 20 })] }));
  else if (t === 'H') kids.push(new Paragraph({ heading: 'Heading2', children: [new TextRun(a)] }));
  else if (t === 'C') kids.push(new Paragraph({ heading: 'Heading2', border: { top: { style: BorderStyle.SINGLE, size: 6, color: 'B0B0B0', space: 6 } }, children: [new TextRun(a)] }));
  else if (t === 'B') kids.push(new Paragraph({ numbering: { reference: 'bul', level: 0 }, children: [new TextRun(a)] }));
  else if (t === 'S') kids.push(new Paragraph({ spacing: { before: 60, after: 60 }, children: [new TextRun({ text: a, italics: true, color: '7A7A7A' })] }));
  else if (t === 'D') {
    const m = b.match(/^(\[[^\]]*\])\s*(.*)$/);
    const runs = [new TextRun({ text: a + '  ', bold: true, color: colors[a] || '000000' })];
    if (m) { runs.push(new TextRun({ text: m[1] + ' ', color: '9A9A9A' })); runs.push(new TextRun(m[2])); }
    else runs.push(new TextRun(b));
    kids.push(new Paragraph({ spacing: { after: 100 }, children: runs }));
  }
}
const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Calibri', size: 23 } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', run: { font: 'Calibri', size: 40, bold: true }, paragraph: { spacing: { before: 0, after: 200 }, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', run: { font: 'Calibri', size: 27, bold: true, color: '333333' }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{ properties: { page: { margin: { top: 1200, bottom: 1200, left: 1300, right: 1300 } } }, children: kids }],
});
Packer.toBuffer(doc).then(b => fs.writeFileSync(process.argv[3], b));
