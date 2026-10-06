'use client';

import React from 'react';
import { UploadCloud, Cpu, Download, ArrowRight } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      step: '01',
      title: 'Upload your PDF',
      description:
        'Drag and drop your PDF or select it from your device. We immediately inspect page counts, structure, and text density.',
      icon: UploadCloud,
      color: 'from-indigo-500 to-blue-500',
    },
    {
      step: '02',
      title: 'Deep Layout & OCR Analysis',
      description:
        'Our engine detects headings, body paragraphs, tables, and images. Scanned pages are automatically recognized and routed to OCR.',
      icon: Cpu,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      step: '03',
      title: 'Download Editable Word Document',
      description:
        'Get a cleanly formatted .docx file ready to edit in Microsoft Word, Google Docs, or LibreOffice. Temporary files are auto-purged.',
      icon: Download,
      color: 'from-cyan-500 to-emerald-500',
    },
  ];

  return (
    <section id="how-it-works" className="py-20 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-bold tracking-wider uppercase px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
            Streamlined 3-Step Process
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white mt-3 tracking-tight">
            How Toolnest Works
          </h2>
          <p className="text-base text-slate-500 dark:text-slate-400 mt-3 leading-relaxed">
            Convert complex documents into fully editable Word documents without messy layout shifts or manual retyping.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {steps.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="relative rounded-3xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 p-8 shadow-xl shadow-slate-200/40 dark:shadow-none hover:-translate-y-1 transition-all duration-300"
              >
                {/* Step badge */}
                <div className="flex items-center justify-between mb-6">
                  <div
                    className={`w-14 h-14 rounded-2xl bg-gradient-to-tr ${item.color} text-white flex items-center justify-center shadow-lg`}
                  >
                    <Icon className="w-7 h-7" />
                  </div>
                  <span className="text-3xl font-black text-slate-200 dark:text-slate-700">
                    {item.step}
                  </span>
                </div>

                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                  {item.title}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  {item.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
