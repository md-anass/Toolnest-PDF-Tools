'use client';

import React from 'react';
import {
  UploadCloud,
  Search,
  FileText,
  ScanText,
  FileCode,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import { ConversionStage } from '@/types/conversion';

interface ConversionProgressProps {
  stage: ConversionStage;
  stageMessage: string;
  progress: number;
  fileName: string;
  isScanned?: boolean;
}

interface StepItem {
  id: ConversionStage;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  showOnlyIfScanned?: boolean;
}

export const ConversionProgress: React.FC<ConversionProgressProps> = ({
  stage,
  stageMessage,
  progress,
  fileName,
  isScanned = false,
}) => {
  const steps: StepItem[] = [
    { id: 'uploading', label: 'Uploading PDF', icon: UploadCloud },
    { id: 'analyzing', label: 'Analyzing document', icon: Search },
    { id: 'extracting', label: 'Extracting content', icon: FileText },
    { id: 'running_ocr', label: 'Running OCR', icon: ScanText, showOnlyIfScanned: true },
    { id: 'reconstructing', label: 'Reconstructing Word', icon: FileCode },
    { id: 'completed', label: 'Complete', icon: CheckCircle2 },
  ];

  // Filter out OCR step if PDF has selectable text and OCR is not needed
  const activeSteps = steps.filter((s) => !s.showOnlyIfScanned || isScanned);

  const getStepStatus = (stepId: ConversionStage) => {
    const stageOrder: ConversionStage[] = [
      'uploading',
      'analyzing',
      'extracting',
      'running_ocr',
      'reconstructing',
      'completed',
    ];

    const currentIdx = stageOrder.indexOf(stage);
    const stepIdx = stageOrder.indexOf(stepId);

    if (stage === 'completed') return 'completed';
    if (stepIdx < currentIdx) return 'completed';
    if (stepIdx === currentIdx) return 'active';
    return 'pending';
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="rounded-3xl bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 p-6 sm:p-10 shadow-xl shadow-slate-200/50 dark:shadow-none transition-all">
        {/* Document Title Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 text-xs font-semibold mb-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Processing Document</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white truncate max-w-md mx-auto">
            {fileName}
          </h3>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-1">
            {stageMessage || 'Converting your file to editable Word format...'}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">
            <span>Overall Progress</span>
            <span className="text-indigo-600 dark:text-indigo-400 font-bold">
              {Math.round(progress)}%
            </span>
          </div>
          <div className="w-full h-3 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden p-0.5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-600 via-indigo-500 to-blue-500 transition-all duration-500 ease-out shadow-sm relative overflow-hidden"
              style={{ width: `${Math.max(progress, 5)}%` }}
            >
              {/* Shimmer animation */}
              <div className="absolute inset-0 bg-white/20 animate-pulse" />
            </div>
          </div>
        </div>

        {/* Step Timeline */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {activeSteps.map((s, idx) => {
            const status = getStepStatus(s.id);
            const Icon = s.icon;

            return (
              <div
                key={s.id}
                className={`p-3 rounded-2xl border text-left transition-all duration-300 flex items-center gap-3 ${
                  status === 'completed'
                    ? 'border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/50 dark:bg-emerald-950/20 text-emerald-800 dark:text-emerald-300'
                    : status === 'active'
                    ? 'border-indigo-400 dark:border-indigo-600 bg-indigo-50/80 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 shadow-md shadow-indigo-500/10'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 text-slate-400 dark:text-slate-600'
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
                    status === 'completed'
                      ? 'bg-emerald-500 text-white'
                      : status === 'active'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-200 dark:bg-slate-800 text-slate-400'
                  }`}
                >
                  {status === 'active' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="text-[10px] uppercase font-bold tracking-wider opacity-70">
                    Step {idx + 1}
                  </div>
                  <div className="text-xs font-semibold truncate">{s.label}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
