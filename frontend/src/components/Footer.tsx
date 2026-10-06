'use client';

import React from 'react';
import { ShieldCheck, Lock, Trash2, Heart } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-slate-900 text-slate-400 border-t border-slate-800 text-sm mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-10 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="h-7 w-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                T
              </div>
              <span className="font-bold text-white text-base">Toolnest</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              High-accuracy PDF to Microsoft Word (.docx) document reconstruction service. Recreates layout, formatting, tables, headings, and images natively.
            </p>
          </div>

          <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/60 md:col-span-2 flex flex-col sm:flex-row items-start sm:items-center gap-4 justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-white text-sm font-semibold flex items-center gap-2">
                  <Lock className="w-3.5 h-3.5 text-emerald-400" />
                  Privacy & Data Hygiene Guarantee
                </h4>
                <p className="text-xs text-slate-400 mt-1">
                  Files are stored in private isolated temporary directories and automatically deleted within 30 minutes. We never index, train on, or retain user documents.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400 shrink-0 bg-slate-900/60 px-3 py-2 rounded-lg border border-slate-700/50">
              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              Auto Purge Active
            </div>
          </div>
        </div>

        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} Toolnest. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <span>FastAPI & Next.js Processing Architecture</span>
            <span>Zero Permanent Retention</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
