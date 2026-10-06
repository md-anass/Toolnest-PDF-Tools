'use client';

import React, { useState } from 'react';
import {
  CheckCircle2,
  FileCheck,
  RefreshCw,
  Trash2,
  Heading,
  AlignLeft,
  Table as TableIcon,
  Image as ImageIcon,
  Cpu,
  Clock,
  HardDrive,
  ShieldCheck,
} from 'lucide-react';
import { ConversionResult as ConversionResultType } from '@/types/conversion';
import { DownloadButton } from './DownloadButton';
import { deleteTemporaryFile } from '@/lib/api';

interface ConversionResultProps {
  result: ConversionResultType;
  onConvertAnother: () => void;
}

export const ConversionResult: React.FC<ConversionResultProps> = ({
  result,
  onConvertAnother,
}) => {
  const [deleted, setDeleted] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleDeleteNow = async () => {
    if (deleting || deleted) return;
    setDeleting(true);
    const success = await deleteTemporaryFile(result.file_id);
    setDeleting(false);
    if (success) {
      setDeleted(true);
    }
  };

  const { extracted_elements } = result;

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="rounded-3xl bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 p-6 sm:p-10 shadow-2xl shadow-indigo-500/5 transition-all text-center">
        {/* Success Icon */}
        <div className="w-20 h-20 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto mb-5 shadow-lg shadow-emerald-500/10 animate-bounce-once">
          <CheckCircle2 className="w-10 h-10" />
        </div>

        <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-2">
          Conversion Complete!
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
          Your document was successfully transformed into an editable Microsoft Word (.docx) file.
        </p>

        {/* Converted Document Card */}
        <div className="rounded-2xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 p-5 mb-8 text-left">
          <div className="flex items-center gap-4 pb-4 border-b border-slate-200/60 dark:border-slate-800">
            <div className="w-12 h-12 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-md shrink-0">
              DOCX
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-base font-bold text-slate-900 dark:text-white truncate">
                {result.docx_filename}
              </h4>
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                <span className="flex items-center gap-1">
                  <HardDrive className="w-3.5 h-3.5" />
                  {formatFileSize(result.file_size_bytes)}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {result.duration_seconds}s
                </span>
                {result.ocr_used && (
                  <>
                    <span>•</span>
                    <span className="inline-flex items-center gap-1 text-indigo-600 dark:text-indigo-400 font-semibold">
                      <Cpu className="w-3.5 h-3.5" />
                      OCR Processed
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Extracted Stats Chips */}
          <div className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
            <div className="p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60">
              <div className="text-slate-400 dark:text-slate-500 text-[10px] uppercase font-semibold">
                Headings
              </div>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center justify-center gap-1 mt-0.5">
                <Heading className="w-3.5 h-3.5 text-indigo-500" />
                {extracted_elements.headings}
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60">
              <div className="text-slate-400 dark:text-slate-500 text-[10px] uppercase font-semibold">
                Paragraphs
              </div>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center justify-center gap-1 mt-0.5">
                <AlignLeft className="w-3.5 h-3.5 text-blue-500" />
                {extracted_elements.paragraphs}
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60">
              <div className="text-slate-400 dark:text-slate-500 text-[10px] uppercase font-semibold">
                Tables
              </div>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center justify-center gap-1 mt-0.5">
                <TableIcon className="w-3.5 h-3.5 text-emerald-500" />
                {extracted_elements.tables}
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60">
              <div className="text-slate-400 dark:text-slate-500 text-[10px] uppercase font-semibold">
                Images
              </div>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center justify-center gap-1 mt-0.5">
                <ImageIcon className="w-3.5 h-3.5 text-purple-500" />
                {extracted_elements.images}
              </div>
            </div>
          </div>
        </div>

        {/* Primary Download & Convert Another Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-6">
          <DownloadButton
            fileId={result.file_id}
            fileName={result.docx_filename}
            downloadUrl={result.download_url}
            size="large"
          />

          <button
            type="button"
            id="convert-another-button"
            onClick={onConvertAnother}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-bold text-sm text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 active:scale-95 transition-all border border-slate-200 dark:border-slate-700"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Convert another PDF</span>
          </button>
        </div>

        {/* Explicit Privacy Cleanup Action */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            Auto-deletes from server in 30 minutes
          </span>

          <button
            type="button"
            id="delete-server-files-button"
            onClick={handleDeleteNow}
            disabled={deleted || deleting}
            className="inline-flex items-center gap-1 text-slate-400 hover:text-rose-500 transition-colors disabled:opacity-50"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{deleted ? 'Deleted from server' : deleting ? 'Deleting...' : 'Delete now'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
