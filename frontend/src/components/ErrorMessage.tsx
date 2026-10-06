'use client';

import React from 'react';
import { AlertCircle, RefreshCw, XCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  onRetry,
  onDismiss,
}) => {
  return (
    <div className="w-full max-w-2xl mx-auto my-6 animate-fade-in">
      <div className="rounded-2xl bg-rose-50/90 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 p-5 sm:p-6 text-rose-900 dark:text-rose-200 shadow-md">
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-xl bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400 shrink-0">
            <AlertCircle className="w-6 h-6" />
          </div>

          <div className="flex-1 min-w-0">
            <h4 className="font-bold text-sm sm:text-base text-rose-950 dark:text-rose-100">
              Unable to complete conversion
            </h4>
            <p className="text-xs sm:text-sm text-rose-800/90 dark:text-rose-300 mt-1 leading-relaxed">
              {message}
            </p>

            <div className="mt-4 flex items-center gap-3">
              {onRetry && (
                <button
                  type="button"
                  id="error-retry-button"
                  onClick={onRetry}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs transition-colors shadow-sm"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Try Again</span>
                </button>
              )}

              {onDismiss && (
                <button
                  type="button"
                  id="error-dismiss-button"
                  onClick={onDismiss}
                  className="px-4 py-2 rounded-xl border border-rose-300 dark:border-rose-800 text-rose-700 dark:text-rose-300 font-semibold text-xs hover:bg-rose-100 dark:hover:bg-rose-900/40 transition-colors"
                >
                  Choose Another PDF
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
