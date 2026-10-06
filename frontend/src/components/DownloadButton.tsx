'use client';

import React, { useState } from 'react';
import { Download, Check, Loader2 } from 'lucide-react';
import { buildDownloadUrl } from '@/lib/api';

interface DownloadButtonProps {
  fileId: string;
  fileName: string;
  downloadUrl?: string;
  size?: 'normal' | 'large';
}

export const DownloadButton: React.FC<DownloadButtonProps> = ({
  fileId,
  fileName,
  downloadUrl,
  size = 'large',
}) => {
  const [downloading, setDownloading] = useState(false);
  const [downloaded, setDownloaded] = useState(false);

  const handleDownload = () => {
    setDownloading(true);
    const targetUrl = downloadUrl || buildDownloadUrl(fileId);

    // Create invisible anchor tag to trigger native download
    const link = document.createElement('a');
    link.href = targetUrl;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => {
      setDownloading(false);
      setDownloaded(true);
      setTimeout(() => setDownloaded(false), 4000);
    }, 1200);
  };

  const isLarge = size === 'large';

  return (
    <button
      type="button"
      id="download-word-button"
      onClick={handleDownload}
      disabled={downloading}
      className={`inline-flex items-center justify-center gap-2.5 font-bold rounded-2xl text-white transition-all shadow-lg active:scale-95 ${
        downloaded
          ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/30'
          : 'bg-gradient-to-r from-indigo-600 via-indigo-500 to-blue-600 hover:from-indigo-500 hover:to-blue-500 shadow-indigo-600/30'
      } ${isLarge ? 'px-8 py-4 text-base w-full sm:w-auto' : 'px-5 py-2.5 text-sm'}`}
    >
      {downloading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Starting Download...</span>
        </>
      ) : downloaded ? (
        <>
          <Check className="w-5 h-5" />
          <span>Downloaded!</span>
        </>
      ) : (
        <>
          <Download className="w-5 h-5" />
          <span>Download Word (.docx)</span>
        </>
      )}
    </button>
  );
};
