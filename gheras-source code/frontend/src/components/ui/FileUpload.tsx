import { cn } from "../../lib/cn";
import { Upload } from "lucide-react";
import { useRef, useState } from "react";

interface FileUploadProps {
  label?: string;
  accept?: string;
  onChange: (file: File | null) => void;
  className?: string;
}

export function FileUpload({ label, accept = "image/*", onChange, className }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    onChange(file);
    if (file) {
      setFileName(file.name);
      if (file.type.startsWith("image/")) {
        const url = URL.createObjectURL(file);
        setPreview(url);
      }
    } else {
      setPreview(null);
      setFileName(null);
    }
  };

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      {label && <span className="text-sm font-medium text-gray-700">{label}</span>}
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="flex flex-col items-center gap-3 rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-6 text-center hover:border-primary hover:bg-emerald-50/30 transition-colors cursor-pointer"
      >
        {preview ? (
          <img src={preview} alt="معاينة" className="h-24 w-24 rounded-lg object-cover" />
        ) : (
          <Upload className="h-8 w-8 text-gray-400" />
        )}
        <div>
          <p className="text-sm font-medium text-gray-600">
            {fileName || "اضغط لرفع صورة"}
          </p>
          <p className="text-xs text-gray-400 mt-1">PNG, JPG حتى 5MB</p>
        </div>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
      />
    </div>
  );
}
