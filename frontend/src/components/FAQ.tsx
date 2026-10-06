'use client';

import React, { useState } from 'react';
import { ChevronDown, HelpCircle } from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
}

export const FAQ: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const faqs: FAQItem[] = [
    {
      question: 'What PDF files can I convert?',
      answer:
        'You can convert standard PDFs containing digital text, forms, multi-page reports, books, scanned paperwork, and document archives. The document can contain text, headings, bullet lists, embedded tables, and images.',
    },
    {
      question: 'Can I convert scanned PDFs?',
      answer:
        'Yes! Toolnest performs automated document analysis on upload. If pages contain little or no extractable digital text and consist of raster image scans, the built-in OCR pipeline extracts the text and layout directly from the visual page image.',
    },
    {
      question: 'Will images and diagrams be preserved?',
      answer:
        'Yes. Embedded images, diagrams, and photos are extracted from the PDF, scaled proportionately to fit standard Word document margins, and inserted into the resulting .docx document in proper reading order.',
    },
    {
      question: 'Will tables be preserved?',
      answer:
        'Yes. Tabular structures detected in your PDF are converted into native Microsoft Word table objects with shaded headers and grid borders, allowing you to edit numbers, text, and add or remove rows in Word.',
    },
    {
      question: 'Are my files stored on your servers?',
      answer:
        'No permanent storage is used. Uploaded PDFs and generated Word files are kept only in temporary, isolated directories during conversion and are automatically deleted after 30 minutes. You can also click "Delete now" immediately after downloading to remove them instantly.',
    },
    {
      question: 'How large can my PDF be?',
      answer:
        'Currently, Toolnest supports PDF documents up to 50 MB in size and with multiple pages. For exceptionally large archives, our background streaming architecture handles processing without browser timeouts.',
    },
  ];

  const toggle = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <section id="faq" className="py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-xs font-bold tracking-wider uppercase px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
            Common Questions
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white mt-3 tracking-tight">
            Frequently Asked Questions
          </h2>
          <p className="text-base text-slate-500 dark:text-slate-400 mt-3 leading-relaxed">
            Everything you need to know about our document conversion, OCR fidelity, and privacy protections.
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div
                key={faq.question}
                className="rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700/80 overflow-hidden shadow-sm transition-all"
              >
                <button
                  type="button"
                  onClick={() => toggle(idx)}
                  className="w-full px-6 py-5 text-left flex items-center justify-between gap-4 focus:outline-none"
                >
                  <span className="font-bold text-sm sm:text-base text-slate-800 dark:text-white">
                    {faq.question}
                  </span>
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 shrink-0 transition-transform duration-200 ${
                      isOpen ? 'rotate-180 bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400' : ''
                    }`}
                  >
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </button>

                {isOpen && (
                  <div className="px-6 pb-5 pt-1 text-sm text-slate-600 dark:text-slate-300 leading-relaxed border-t border-slate-100 dark:border-slate-700/40 animate-fade-in">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
