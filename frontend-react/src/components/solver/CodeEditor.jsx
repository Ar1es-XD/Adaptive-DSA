import React from 'react';
import Editor from '@monaco-editor/react';

export default function CodeEditor({ code, onChange, onSubmit, submitting }) {
  return (
    <div className="h-full flex flex-col">
      {/* Editor */}
      <Editor
        height="400px"
        language="javascript"
        value={code}
        onChange={(value) => onChange(value || '')}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          wordWrap: 'on',
          autoIndent: 'full',
          formatOnPaste: true,
          tabSize: 2
        }}
        theme="light"
      />

      {/* Controls */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 flex gap-3">
        <button
          onClick={onSubmit}
          disabled={submitting}
          className={`flex-1 px-4 py-2 font-medium rounded-lg text-white transition ${
            submitting
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-green-500 hover:bg-green-600'
          }`}
        >
          {submitting ? 'Submitting...' : 'Submit Solution'}
        </button>
      </div>
    </div>
  );
}
