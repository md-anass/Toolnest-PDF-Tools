'use client';

import React, { ChangeEvent, DragEvent, useRef, useState } from 'react';
import { ArrowDownToLine, FileText, LoaderCircle, Trash2, UploadCloud } from 'lucide-react';
import { runDocumentTool } from '@/lib/api';

export type DocumentToolOperation = 'merge' | 'split' | 'compress' | 'to-pdf';

interface DocumentToolsProps {
  operation: DocumentToolOperation;
}

const operationCopy: Record<DocumentToolOperation, { title: string; action: string; accept: string; multiple: boolean; description: string }> = {
  merge: {
    title: 'Merge PDF files',
    action: 'Merge PDFs',
    accept: '.pdf,application/pdf',
    multiple: true,
    description: 'Choose 2 to 20 PDFs. They will be combined in the order shown.',
  },
  split: {
    title: 'Split a PDF',
    action: 'Split into pages',
    accept: '.pdf,application/pdf',
    multiple: false,
    description: 'Each page becomes a separate PDF in one ZIP download.',
  },
  compress: {
    title: 'Compress a PDF',
    action: 'Compress PDF',
    accept: '.pdf,application/pdf',
    multiple: false,
    description: 'Reduce redundant PDF data while retaining page content.',
  },
  'to-pdf': {
    title: 'Convert files to PDF',
    action: 'Convert to PDF',
    accept: '.doc,.docx,.odt,.rtf,.ppt,.pptx,.odp,.xls,.xlsx,.ods,.csv,.txt,.png,.jpg,.jpeg,.tif,.tiff,.bmp,.webp,.pdf',
    multiple: false,
    description: 'Supports Word, PowerPoint, Excel, OpenDocument, RTF, CSV, TXT, and common image files. Office formats need LibreOffice on the server.',
  },
};

const MAX_FILE_SIZE = 50 * 1024 * 1024;
const MAX_TOTAL_SIZE = 100 * 1024 * 1024;
const MAX_MERGE_FILES = 20;

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentTools({ operation }: DocumentToolsProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const copy = operationCopy[operation];

  const addFiles = (selected: FileList | File[]) => {
    const incoming = Array.from(selected);
    setError(null);
    const next = copy.multiple ? [...files, ...incoming] : incoming.slice(0, 1);
    if (next.length > MAX_MERGE_FILES) {
      setError(`Choose no more than ${MAX_MERGE_FILES} PDFs.`);
      return;
    }
    if (next.some((file) => file.size > MAX_FILE_SIZE)) {
      setError('Each file must be 50 MB or smaller.');
      return;
    }
    if (next.reduce((total, file) => total + file.size, 0) > MAX_TOTAL_SIZE) {
      setError('The combined upload must be 100 MB or smaller.');
      return;
    }
    if (operation === 'merge' && next.some((file) => !file.name.toLowerCase().endsWith('.pdf'))) {
      setError('Only PDF files can be merged.');
      return;
    }
    if (operation === 'split' || operation === 'compress') {
      if (next.some((file) => !file.name.toLowerCase().endsWith('.pdf'))) {
        setError('Choose a PDF file for this operation.');
        return;
      }
    }
    setFiles(next);
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.length) addFiles(event.target.files);
    event.target.value = '';
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    if (!isProcessing && event.dataTransfer.files.length) addFiles(event.dataTransfer.files);
  };

  const removeFile = (index: number) => {
    setFiles((current) => current.filter((_, fileIndex) => fileIndex !== index));
    setError(null);
  };

  const processFiles = async () => {
    setError(null);
    setIsProcessing(true);
    try {
      await runDocumentTool(operation, files);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to process these files.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <section className="mx-auto w-full max-w-3xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-200/50 dark:border-slate-700 dark:bg-slate-800 dark:shadow-none">
      <div className="border-b border-slate-100 px-6 py-5 dark:border-slate-700 sm:px-8">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">{copy.title}</h2>
        <p className="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{copy.description}</p>
      </div>

      <div className="p-6 sm:p-8">
        <input
          ref={inputRef}
          type="file"
          accept={copy.accept}
          multiple={copy.multiple}
          onChange={handleInputChange}
          className="hidden"
          disabled={isProcessing}
        />
        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click();
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`cursor-pointer rounded-xl border-2 border-dashed px-5 py-8 text-center transition-colors ${isDragOver ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/40' : 'border-slate-300 bg-slate-50/70 hover:border-indigo-400 dark:border-slate-600 dark:bg-slate-900/40'}`}
        >
          <UploadCloud className="mx-auto h-8 w-8 text-indigo-600 dark:text-indigo-400" />
          <p className="mt-3 text-sm font-semibold text-slate-800 dark:text-slate-100">
            {files.length ? 'Add or replace files' : 'Drop files here or browse'}
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Up to 50 MB per file</p>
        </div>

        {files.length > 0 && (
          <ul className="mt-5 divide-y divide-slate-100 rounded-lg border border-slate-200 dark:divide-slate-700 dark:border-slate-700">
            {files.map((file, index) => (
              <li key={`${file.name}-${file.lastModified}-${index}`} className="flex items-center gap-3 px-3 py-3">
                <FileText className="h-5 w-5 shrink-0 text-indigo-600 dark:text-indigo-400" />
                <span className="min-w-0 flex-1 truncate text-sm font-medium text-slate-800 dark:text-slate-100">{file.name}</span>
                <span className="shrink-0 text-xs text-slate-500">{formatSize(file.size)}</span>
                <button
                  type="button"
                  title={`Remove ${file.name}`}
                  onClick={() => removeFile(index)}
                  disabled={isProcessing}
                  className="rounded p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50 dark:hover:bg-rose-950/40"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        )}

        {error && <p role="alert" className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">{error}</p>}

        <div className="mt-6 flex flex-col-reverse items-center justify-between gap-3 sm:flex-row">
          <p className="text-xs text-slate-500 dark:text-slate-400">Files are removed from the server after processing.</p>
          <button
            type="button"
            onClick={processFiles}
            disabled={files.length === 0 || isProcessing || (operation === 'merge' && files.length < 2)}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
          >
            {isProcessing ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ArrowDownToLine className="h-4 w-4" />}
            {isProcessing ? 'Processing...' : copy.action}
          </button>
        </div>
      </div>
    </section>
  );
}
