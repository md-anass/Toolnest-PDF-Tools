'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Header,
  Footer,
  PDFUploader,
  FilePreview,
  ConversionProgress,
  ConversionResult,
  ErrorMessage,
  HowItWorks,
  FeatureCard,
  FAQ,
} from '@/components';
import { DocumentTools, type DocumentToolOperation } from '@/components/DocumentTools';
import {
  ConversionStage,
  DocumentAnalysis,
  ConversionResult as ConversionResultType,
} from '@/types/conversion';
import {
  analyzePDFFile,
  uploadAndStartConversion,
  fetchJobStatus,
  checkBackendHealth,
} from '@/lib/api';
import { FileOutput, FileStack, FileText, Minimize2, Scissors, Sparkles } from 'lucide-react';

type ActiveTool = 'word' | DocumentToolOperation;

const toolOptions: { id: ActiveTool; label: string; icon: typeof FileText }[] = [
  { id: 'word', label: 'PDF to Word', icon: FileText },
  { id: 'merge', label: 'Merge', icon: FileStack },
  { id: 'split', label: 'Split', icon: Scissors },
  { id: 'compress', label: 'Compress', icon: Minimize2 },
  { id: 'to-pdf', label: 'Convert to PDF', icon: FileOutput },
];

export default function Home() {
  const [activeTool, setActiveTool] = useState<ActiveTool>('word');
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [stage, setStage] = useState<ConversionStage>('idle');
  const [stageMessage, setStageMessage] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<ConversionResultType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ocrAvailable, setOcrAvailable] = useState<boolean>(true);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth().then((health) => {
      if (health) {
        setOcrAvailable(Boolean(health.ocr_available));
      }
    });

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setResult(null);
    setStage('idle');
    setAnalysis(null);

    // Run quick background pre-analysis for page count
    setIsAnalyzing(true);
    try {
      const data = await analyzePDFFile(selectedFile);
      setAnalysis(data);
    } catch (err) {
      console.warn('Pre-analysis skipped or non-fatal:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRemoveFile = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    setFile(null);
    setAnalysis(null);
    setResult(null);
    setError(null);
    setStage('idle');
    setProgress(0);
    setStageMessage('');
  };

  const handleConvert = async () => {
    if (!file) return;

    setError(null);
    setStage('uploading');
    setStageMessage('Uploading PDF...');
    setProgress(5);

    try {
      // 1. Upload file and initiate conversion job
      const uploadResp = await uploadAndStartConversion(file, (percent) => {
        // Upload progress (0 - 20%)
        setProgress(Math.round((percent * 0.2)));
      });

      const jobId = uploadResp.job_id;
      setStage('analyzing');
      setStageMessage('Analyzing document...');
      setProgress(25);

      // 2. Poll job status
      const poll = async () => {
        try {
          const jobData = await fetchJobStatus(jobId);

          if (jobData.analysis && !analysis) {
            setAnalysis(jobData.analysis);
          }

          if (jobData.status === 'processing') {
            setStage(jobData.stage);
            setStageMessage(jobData.stage_message || 'Processing document...');
            setProgress(jobData.progress || 35);
          } else if (jobData.status === 'completed') {
            if (pollingRef.current) clearInterval(pollingRef.current);
            setStage('completed');
            setStageMessage('Conversion complete');
            setProgress(100);
            if (jobData.result) {
              setResult(jobData.result);
            }
          } else if (jobData.status === 'failed') {
            if (pollingRef.current) clearInterval(pollingRef.current);
            setStage('failed');
            setError(
              jobData.error_message ||
                'Unable to convert this PDF. The document may be corrupted or password-protected.'
            );
          }
        } catch (pollErr: unknown) {
          if (pollingRef.current) clearInterval(pollingRef.current);
          setStage('failed');
          setError(pollErr instanceof Error ? pollErr.message : 'Connection lost while converting PDF.');
        }
      };

      // Poll every 700ms
      pollingRef.current = setInterval(poll, 700);
      // Run first poll immediately
      poll();

    } catch (err: unknown) {
      setStage('failed');
      setError(
        (err instanceof Error ? err.message : null) ||
          'Unable to convert this PDF. Please verify your connection and try again.'
      );
    }
  };

  const isConverting =
    stage === 'uploading' ||
    stage === 'analyzing' ||
    stage === 'extracting' ||
    stage === 'running_ocr' ||
    stage === 'reconstructing';

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Header */}
      <Header ocrAvailable={ocrAvailable} />

      {/* Main Container */}
      <main className="flex-1">
        {/* Hero & Converter Section */}
        <section className="relative pt-12 pb-20 sm:pt-20 sm:pb-28 overflow-hidden">
          {/* Ambient Glow Elements */}
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-tr from-indigo-500/10 via-blue-500/10 to-purple-500/10 blur-3xl pointer-events-none -z-10 rounded-full" />

          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* Hero Copy */}
            <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-14">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-950/70 border border-indigo-200/80 dark:border-indigo-800/80 text-indigo-700 dark:text-indigo-300 text-xs font-semibold mb-4 shadow-sm">
                <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                <span>Document conversion and PDF tools</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 dark:text-white leading-[1.15]">
                {activeTool === 'word' ? 'Convert PDF to Word' : toolOptions.find((tool) => tool.id === activeTool)?.label}
              </h1>

              <p className="mt-4 text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl mx-auto">
                {activeTool === 'word'
                  ? 'Turn your PDF documents into editable Word files while preserving text, images, and document structure.'
                  : 'Merge, split, compress, or convert documents and images to PDF in one secure workspace.'}
              </p>
            </div>

            <div className="mb-8 flex flex-wrap justify-center gap-2" role="tablist" aria-label="Document tools">
              {toolOptions.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={activeTool === id}
                  onClick={() => setActiveTool(id)}
                  className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-semibold transition-colors ${activeTool === id ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm' : 'border-slate-200 bg-white/80 text-slate-700 hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-200 dark:hover:border-indigo-600'}`}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </button>
              ))}
            </div>

            {activeTool === 'word' && error && (
              <ErrorMessage
                message={error}
                onRetry={file ? handleConvert : undefined}
                onDismiss={handleRemoveFile}
              />
            )}

            {/* Interactive Conversion Flow States */}
            <div className="transition-all duration-300">
              {activeTool !== 'word' ? (
                <DocumentTools key={activeTool} operation={activeTool} />
              ) : stage === 'completed' && result ? (
                /* State 6: Completed Result Card */
                <ConversionResult
                  result={result}
                  onConvertAnother={handleRemoveFile}
                />
              ) : isConverting ? (
                /* States 1 to 5: Progress Timeline */
                <ConversionProgress
                  stage={stage}
                  stageMessage={stageMessage}
                  progress={progress}
                  fileName={file ? file.name : 'document.pdf'}
                  isScanned={analysis?.is_scanned || stage === 'running_ocr'}
                />
              ) : file ? (
                /* Uploaded File Preview Card */
                <FilePreview
                  file={file}
                  analysis={analysis}
                  isAnalyzing={isAnalyzing}
                  onRemove={handleRemoveFile}
                  onConvert={handleConvert}
                  isProcessing={isConverting}
                />
              ) : (
                /* Empty Upload Zone */
                <PDFUploader
                  onFileSelect={handleFileSelect}
                  isProcessing={isConverting}
                />
              )}
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <HowItWorks />

        {/* Features Section */}
        <FeatureCard />

        {/* FAQ Section */}
        <FAQ />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
