/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  Calculator, 
  Terminal, 
  FileText, 
  Download, 
  ExternalLink, 
  CheckCircle2, 
  Copy, 
  AlertCircle,
  Github,
  MapPin
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const CodeBlock = ({ code, language }: { code: string, language: string }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group bg-slate-900 rounded-lg overflow-hidden my-4 border border-slate-800">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800/50 border-b border-slate-700">
        <span className="text-xs font-mono text-slate-400">{language}</span>
        <button 
          onClick={copyToClipboard}
          className="p-1.5 hover:bg-slate-700 rounded-md transition-colors text-slate-400 hover:text-white"
          title="Copy to clipboard"
        >
          {copied ? <CheckCircle2 size={16} className="text-emerald-400" /> : <Copy size={16} />}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm font-mono text-slate-300 leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export default function App() {
  const colabSetupCode = `!git clone https://github.com/sonvuhong-qa/distance-calculator/
%cd distance-calculator
!chmod +x colab_setup.sh
!./colab_setup.sh`;

  const colabRunCode = `!./.venv/bin/python distance_calculator_tool.py \\
  --csv "Employees_input_demo.csv" \\
  --company-address "Your Company Address" \\
  --headless`;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-indigo-600 text-xl">
            <Calculator className="w-6 h-6" />
            <span>DistCalc</span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#features" className="hover:text-indigo-600 transition-colors">Features</a>
            <a href="#colab" className="hover:text-indigo-600 transition-colors">Colab Setup</a>
            <a href="#usage" className="hover:text-indigo-600 transition-colors">Usage</a>
          </nav>
          <div className="flex items-center gap-4">
            <a 
              href="https://github.com/sonvuhong-qa/distance-calculator" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-2 text-slate-500 hover:text-slate-900 transition-colors"
            >
              <Github className="w-5 h-5" />
            </a>
            <button className="bg-indigo-600 text-white px-4 py-2 rounded-full text-sm font-semibold hover:bg-indigo-700 transition-all shadow-sm hover:shadow-md active:scale-95">
              Get Started
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12 space-y-24">
        {/* Hero Section */}
        <section className="text-center space-y-6 max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight">
              Calculate Distances at <span className="text-indigo-600">Scale</span>
            </h1>
            <p className="mt-6 text-xl text-slate-600 leading-relaxed">
              A powerful Python tool designed to automate distance calculations between multiple addresses and a central location using Google Maps. Optimized for high performance and reliability.
            </p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="flex flex-wrap items-center justify-center gap-4 pt-4"
          >
            <div className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-700 rounded-full text-sm font-medium border border-indigo-100">
              <CheckCircle2 size={16} />
              <span>Google Colab Ready</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium border border-emerald-100">
              <CheckCircle2 size={16} />
              <span>Parallel Processing</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-700 rounded-full text-sm font-medium border border-amber-100">
              <CheckCircle2 size={16} />
              <span>Headless Support</span>
            </div>
          </motion.div>
        </section>

        {/* Features Grid */}
        <section id="features" className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: <Terminal className="w-6 h-6 text-indigo-600" />,
              title: "CLI Driven",
              description: "Simple command-line interface with support for CSV inputs and custom parameters."
            },
            {
              icon: <MapPin className="w-6 h-6 text-indigo-600" />,
              title: "Maps Integration",
              description: "Uses Selenium to interact with Google Maps for accurate, real-world distance data."
            },
            {
              icon: <ExternalLink className="w-6 h-6 text-indigo-600" />,
              title: "Colab Optimized",
              description: "Specialized setup for Google Colab environments including headless browser configuration."
            }
          ].map((feature, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -5 }}
              className="p-8 bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl transition-all"
            >
              <div className="mb-4 p-3 bg-indigo-50 rounded-xl w-fit">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-slate-600 leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </section>

        {/* Colab Setup Section */}
        <section id="colab" className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="grid md:grid-cols-2">
            <div className="p-12 space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-600 text-white rounded-md text-xs font-bold uppercase tracking-wider">
                Step 1
              </div>
              <h2 className="text-3xl font-bold">Setup in Google Colab</h2>
              <p className="text-slate-600 leading-relaxed">
                Running the distance calculator in Google Colab is straightforward. Copy and run this block in a new cell to clone the repository and install all necessary dependencies.
              </p>
              <div className="flex items-center gap-4 text-sm font-medium text-slate-500">
                <div className="flex items-center gap-1.5">
                  <FileText size={16} />
                  <span>requirements.txt</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Terminal size={16} />
                  <span>colab_setup.sh</span>
                </div>
              </div>
            </div>
            <div className="bg-slate-950 p-6 flex flex-col justify-center">
              <CodeBlock code={colabSetupCode} language="bash" />
            </div>
          </div>
        </section>

        {/* Usage Section */}
        <section id="usage" className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="grid md:grid-cols-2 md:divide-x divide-slate-200">
            <div className="bg-slate-950 p-6 flex flex-col justify-center order-2 md:order-1">
              <CodeBlock code={colabRunCode} language="bash" />
            </div>
            <div className="p-12 space-y-6 order-1 md:order-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-600 text-white rounded-md text-xs font-bold uppercase tracking-wider">
                Step 2
              </div>
              <h2 className="text-3xl font-bold">Run the Calculator</h2>
              <p className="text-slate-600 leading-relaxed">
                Once the environment is ready, you can run the tool using the virtual environment's Python. Make sure to provide your input CSV and the target company address.
              </p>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="mt-1 p-1 bg-emerald-100 text-emerald-700 rounded-full">
                    <CheckCircle2 size={14} />
                  </div>
                  <p className="text-sm text-slate-600">Use <code className="bg-slate-100 px-1 rounded text-indigo-600">--csv</code> to specify your input file.</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-1 p-1 bg-emerald-100 text-emerald-700 rounded-full">
                    <CheckCircle2 size={14} />
                  </div>
                  <p className="text-sm text-slate-600">Use <code className="bg-slate-100 px-1 rounded text-indigo-600">--company-address</code> for the destination.</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-1 p-1 bg-emerald-100 text-emerald-700 rounded-full">
                    <CheckCircle2 size={14} />
                  </div>
                  <p className="text-sm text-slate-600">Add <code className="bg-slate-100 px-1 rounded text-indigo-600">--headless</code> for faster execution in Colab.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Files Section */}
        <section className="space-y-8">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold">Project Files</h2>
            <p className="mt-4 text-slate-600">
              The repository contains everything you need to get started. You can also find these files in the file explorer.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { name: "distance_calculator_tool.py", type: "Python Script", icon: <Terminal size={20} /> },
              { name: "requirements.txt", type: "Dependencies", icon: <FileText size={20} /> },
              { name: "Employees_input_demo.csv", type: "Sample Data", icon: <FileText size={20} /> },
              { name: "colab_setup.sh", type: "Setup Script", icon: <Terminal size={20} /> }
            ].map((file, i) => (
              <div key={i} className="p-6 bg-white rounded-2xl border border-slate-200 flex items-center gap-4 group hover:border-indigo-300 transition-colors">
                <div className="p-3 bg-slate-50 text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 rounded-xl transition-colors">
                  {file.icon}
                </div>
                <div>
                  <div className="font-semibold text-sm truncate max-w-[150px]">{file.name}</div>
                  <div className="text-xs text-slate-500">{file.type}</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Warning Section */}
        <section className="p-8 bg-amber-50 border border-amber-100 rounded-3xl flex flex-col md:flex-row items-center gap-6">
          <div className="p-4 bg-amber-100 text-amber-700 rounded-2xl">
            <AlertCircle size={32} />
          </div>
          <div className="space-y-2 text-center md:text-left">
            <h4 className="text-lg font-bold text-amber-900">Important Note on Selenium</h4>
            <p className="text-amber-800 leading-relaxed">
              This tool uses Selenium to automate a web browser. In Google Colab, it must run in <strong>headless mode</strong>. We've updated the script to automatically detect Colab and apply the correct settings.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-12">
        <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex items-center gap-2 font-bold text-slate-400 text-lg">
            <Calculator className="w-5 h-5" />
            <span>DistCalc</span>
          </div>
          <p className="text-sm text-slate-500">
            © 2026 Distance Calculator Tool. Built for Google AI Studio.
          </p>
          <div className="flex items-center gap-6">
            <a href="https://github.com/sonvuhong-qa/distance-calculator" className="text-slate-400 hover:text-slate-900 transition-colors"><Github size={20} /></a>
          </div>
        </div>
      </footer>
    </div>
  );
}
