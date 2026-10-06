'use client';

import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, FileText, Shield, ArrowUpRight, AlertCircle } from 'lucide-react';

interface PDFUploaderProps {
  onFileSelect: (file: File) => void;
  isProcessing?: boolean;
  maxSizeBytes?: number; // default 50MB
}

export const PDFUploader: React.FC<PDFUploaderProps> = ({
  onFileSelect,
  isProcessing = false,
  maxSizeBytes = 50 * 1024 * 1024,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleValidateAndSelect = (file: File) => {
    setValidationError(null);

    // 1. File extension & type validation
    const isPDF =
      file.name.toLowerCase().endsWith('.pdf') ||
      file.type === 'application/pdf';

    if (!isPDF) {
      setValidationError('Please select a valid PDF document (.pdf).');
      return;
    }

    // 2. Size validation
    if (file.size > maxSizeBytes) {
      const maxMB = Math.round(maxSizeBytes / (1024 * 1024));
      setValidationError(`File exceeds maximum allowed size of ${maxMB}MB.`);
      return;
    }

    if (file.size < 64) {
      setValidationError('The selected PDF file is empty or corrupted.');
      return;
    }

    onFileSelect(file);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isProcessing) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (isProcessing) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      handleValidateAndSelect(file);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      handleValidateAndSelect(file);
    }
    // reset input so same file can be re-selected if removed
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const triggerPicker = () => {
    if (!isProcessing && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="w-full">
      <div
        id="pdf-drop-zone"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={triggerPicker}
        className={`relative group cursor-pointer rounded-3xl border-2 border-dashed p-8 sm:p-14 text-center transition-all duration-300 ${
          isDragOver
            ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01] shadow-2xl shadow-indigo-500/10'
            : 'border-slate-300 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500 bg-white/70 dark:bg-slate-800/50 hover:bg-slate-50/80 dark:hover:bg-slate-800/80 shadow-xl shadow-slate-200/50 dark:shadow-none'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleFileInputChange}
          disabled={isProcessing}
          id="pdf-file-input"
        />

        <div className="flex flex-col items-center justify-center max-w-md mx-auto">
          {/* Animated PDF Icon Badge */}
          <div
            className={`w-20 h-20 sm:w-24 sm:h-24 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300 ${
              isDragOver
                ? 'bg-indigo-600 text-white scale-110 shadow-lg shadow-indigo-500/30'
                : 'bg-gradient-to-tr from-indigo-50 to-blue-50 dark:from-indigo-950/60 dark:to-slate-800 text-indigo-600 dark:text-indigo-400 group-hover:scale-105 group-hover:shadow-md'
            }`}
          >
            <UploadCloud className="w-10 h-10 sm:w-12 sm:h-12 stroke-[1.75]" />
          </div>

          <h3 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white mb-2 tracking-tight">
            Drop your PDF here
          </h3>

          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
            or browse files from your computer or device
          </p>

          {/* Primary Select Button */}
          <button
            type="button"
            id="select-pdf-button"
            onClick={(e) => {
              e.stopPropagation();
              triggerPicker();
            }}
            disabled={isProcessing}
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-blue-600 hover:from-indigo-500 hover:to-blue-500 active:scale-95 transition-all shadow-lg shadow-indigo-600/25 ring-1 ring-white/20"
          >
            <FileText className="w-4 h-4" />
            <span>Select PDF</span>
          </button>

          {/* Format / Limits Info */}
          <div className="mt-6 flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <span className="inline-flex items-center gap-1 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
              PDF format only
            </span>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <span>Up to 50 MB</span>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <span>Text, Scans & Tables</span>
          </div>
        </div>

        {/* Validation Error Toast */}
        {validationError && (
          <div className="mt-6 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs font-medium animate-shake">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{validationError}</span>
          </div>
        )}
      </div>

      {/* Privacy message explicitly placed near the uploader */}
      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-100/70 dark:bg-slate-800/40 rounded-xl px-4 py-2.5 border border-slate-200/60 dark:border-slate-800">
        <Shield className="w-4 h-4 text-emerald-500 shrink-0" />
        <span>
          Your files are processed securely and temporary files are automatically deleted.
        </span>
      </div>
    </div>
  );
};
