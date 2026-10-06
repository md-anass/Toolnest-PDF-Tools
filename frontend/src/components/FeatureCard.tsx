'use client';

import React from 'react';
import {
  FileText,
  ScanText,
  Type,
  Image as ImageIcon,
  Table as TableIcon,
  Layers,
  Zap,
  ShieldCheck,
} from 'lucide-react';

interface FeatureItem {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  tag?: string;
}

export const FeatureCard: React.FC = () => {
  const features: FeatureItem[] = [
    {
      title: 'Editable Word Documents',
      description:
        'Converts into genuine Microsoft Word (.docx) files with paragraphs, runs, fonts, and headings rather than flattened images or text dumps.',
      icon: FileText,
      tag: 'Native .docx',
    },
    {
      title: 'OCR for Scanned PDFs',
      description:
        'Intelligent document analysis recognizes non-selectable scanned pages and runs high-accuracy Optical Character Recognition.',
      icon: ScanText,
      tag: 'Tesseract Powered',
    },
    {
      title: 'Typography & Style Preservation',
      description:
        'Preserves font sizes, bold, italic, line spacing, and paragraph alignment across both simple notes and complex reports.',
      icon: Type,
    },
    {
      title: 'Image Extraction & Placement',
      description:
        'Extracts embedded diagrams and photographs at original resolution and positions them seamlessly inline with surrounding content.',
      icon: ImageIcon,
    },
    {
      title: 'Basic Table Reconstruction',
      description:
        'Detects tabular layouts and generates structured Word tables with shaded header rows and clean cell borders.',
      icon: TableIcon,
    },
    {
      title: 'Multi-Page Support',
      description:
        'Flawlessly processes multi-page manuals, proposals, and documents with clean page breaks and sequential flow.',
      icon: Layers,
    },
    {
      title: 'Fast Asynchronous Processing',
      description:
        'Non-blocking background pipeline delivers progress updates in real-time without freezing or timing out.',
      icon: Zap,
      tag: 'Async Queue',
    },
    {
      title: 'Secure Temporary Processing',
      description:
        'Strict zero-retention guarantee. Uploaded PDFs and generated DOCX files are isolated and automatically purged within 30 minutes.',
      icon: ShieldCheck,
      tag: 'Zero Retention',
    },
  ];

  return (
    <section id="features" className="py-20 bg-slate-50/70 dark:bg-slate-900/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-bold tracking-wider uppercase px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
            Engine Capabilities
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white mt-3 tracking-tight">
            Engineered for Precision & Fidelity
          </h2>
          <p className="text-base text-slate-500 dark:text-slate-400 mt-3 leading-relaxed">
            Everything you need to turn static PDFs into living, collaborative documents.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className="rounded-3xl bg-white dark:bg-slate-800/90 border border-slate-200/80 dark:border-slate-700/80 p-6 shadow-lg shadow-slate-200/40 dark:shadow-none hover:shadow-xl hover:border-indigo-300 dark:hover:border-indigo-600 transition-all duration-300 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-100 dark:border-indigo-800/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                      <Icon className="w-6 h-6" />
                    </div>
                    {f.tag && (
                      <span className="text-[10px] font-bold tracking-wide uppercase px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                        {f.tag}
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">
                    {f.title}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                    {f.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
