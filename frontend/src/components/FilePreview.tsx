'use client';

import React from 'react';
import {
  FileText,
  Trash2,
  ArrowRight,
  Layers,
  Sparkles,
  FileCheck2,
  ScanText,
  Loader2,
} from 'lucide-react';
import { DocumentAnalysis } from '@/types/conversion';

interface FilePreviewProps {
  file: File;
  pageCount?: number;
  analysis?: DocumentAnalysis | null;
  isAnalyzing?: boolean;
  onRemove: () => void;
  onConvert: () => void;
  isProcessing?: boolean;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  file,
  pageCount,
  analysis,
  isAnalyzing = false,
  onRemove,
  onConvert,
  isProcessing = false,
}) => {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const detectedPages = analysis?.page_count || pageCount;
  const isScanned = analysis?.is_scanned;

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="rounded-3xl bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 p-6 sm:p-8 shadow-xl shadow-slate-200/50 dark:shadow-none transition-all">
        <div className="flex items-start justify-between gap-4 pb-6 border-b border-slate-100 dark:border-slate-700/60">
          <div className="flex items-center gap-4 min-w-0">
            {/* File Icon */}
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500/10 to-blue-500/10 dark:from-indigo-900/40 dark:to-blue-900/40 border border-indigo-200/50 dark:border-indigo-700/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400 shrink-0">
              <FileText className="w-7 h-7" />
            </div>

            {/* File Details */}
            <div className="min-w-0">
              <h4 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white truncate">
                {file.name}
              </h4>
              <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-slate-500 dark:text-slate-400">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {formatFileSize(file.size)}
                </span>
                <span>•</span>
                {isAnalyzing ? (
                  <span className="inline-flex items-center gap-1 text-indigo-500 font-medium">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Inspecting pages...
                  </span>
                ) : detectedPages ? (
                  <span className="inline-flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300">
                    <Layers className="w-3.5 h-3.5 text-indigo-500" />
                    {detectedPages} {detectedPages === 1 ? 'page' : 'pages'}
                  </span>
                ) : (
                  <span>Ready to convert</span>
                )}

                {/* Scanned / Text badge */}
                {analysis && (
                  <>
                    <span>•</span>
                    {isScanned ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-[11px] font-semibold">
                        <ScanText className="w-3 h-3" />
                        Scanned (OCR)
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-[11px] font-semibold">
                        <FileCheck2 className="w-3 h-3" />
                        Selectable Text
                      </span>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Remove File Button */}
          <button
            type="button"
            id="remove-file-button"
            onClick={onRemove}
            disabled={isProcessing}
            title="Remove file"
            className="p-2.5 rounded-xl text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>

        {/* Action Bar */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-500 shrink-0" />
            <span>Converts headings, paragraphs, tables & images into Word .docx</span>
          </div>

          <button
            type="button"
            id="convert-pdf-button"
            onClick={onConvert}
            disabled={isProcessing}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-blue-600 hover:from-indigo-500 hover:to-blue-500 active:scale-95 transition-all shadow-lg shadow-indigo-600/25 ring-1 ring-white/20"
          >
            <span>Convert to Word</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
