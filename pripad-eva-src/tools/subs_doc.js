const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, LevelFormat, AlignmentType, BorderStyle, PageBreak } = require('docx');
const data = JSON.parse(fs.readFileSync('/tmp/subs_doc.json', 'utf8'));
const C = { 'EVA': '8B1E3F', 'NIKOL': '1F4E79', 'NIKOL (v duchu)': '5B7FA6', 'BABKA': '5A4A2F', 'SPRIEVODCA': '555555', 'CENTRÁLA': '2E7D5B', 'LUCY': '6A4FB0', 'KOLLÁR': '3D7A47' };
const kids = [
  new Paragraph({ heading: 'Title', children: [new TextRun('Prípad Eva – titulky na kontrolu')] }),
  new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: 'Ako na to:', bold: true })] }),
  new Paragraph({ numbering: { reference: 'num', level: 0 }, children: [new TextRun('Pri každej scéne prepíš repliky presne tak, ako ich postava hovorí v nahrávke.')] }),
  new Paragraph({ numbering: { reference: 'num', level: 0 }, children: [new TextRun('Zachovaj poradie a formát „POSTAVA: text“. Jedna replika = jeden riadok.')] }),
  new Paragraph({ numbering: { reference: 'num', level: 0 }, children: [new TextRun('Repliku, ktorá v nahrávke nie je, zmaž. Chýbajúcu dopíš na správne miesto.')] }),
  new Paragraph({ numbering: { reference: 'num', level: 0 }, children: [new TextRun('Názov scény a kód v zátvorke nemeň, podľa neho viem, ku ktorej nahrávke text patrí.')] }),
  new Paragraph({ spacing: { before: 120, after: 200 }, children: [new TextRun({ text: 'Postavy: EVA, NIKOL, NIKOL (v duchu), BABKA, SPRIEVODCA, CENTRÁLA, LUCY, KOLLÁR', color: '777777', size: 20 })] }),
];
data.forEach((sc, i) => {
  kids.push(new Paragraph({ heading: 'Heading2', border: i ? { top: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC', space: 8 } } : undefined,
    children: [new TextRun(sc.name + '  '), new TextRun({ text: '(' + sc.id + ')', color: '999999', size: 20, bold: false })] }));
  if (!sc.lines.length) kids.push(new Paragraph({ children: [new TextRun({ text: '(bez titulkov)', italics: true, color: '999999' })] }));
  sc.lines.forEach(([w, t]) => kids.push(new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: w + ': ', bold: true, color: C[w] || '000000' }), new TextRun(t)] })));
});
const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Calibri', size: 23 } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', run: { font: 'Calibri', size: 40, bold: true }, paragraph: { spacing: { before: 0, after: 200 }, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', run: { font: 'Calibri', size: 27, bold: true, color: '333333' }, paragraph: { spacing: { before: 300, after: 120 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: 'num', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{ properties: { page: { margin: { top: 1200, bottom: 1200, left: 1300, right: 1300 } } }, children: kids }],
});
Packer.toBuffer(doc).then(b => fs.writeFileSync(process.argv[2], b));
