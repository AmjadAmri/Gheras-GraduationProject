import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";

function friendlyError(raw: string): string {
  const msg = raw.toLowerCase();
  if (msg.includes("invalid credentials") || msg.includes("invalid")) {
    return "البريد الإلكتروني أو كلمة المرور غير صحيحة";
  }
  if (msg.includes("required") || msg.includes("blank")) {
    return "يرجى ملء جميع الحقول";
  }
  if (msg.includes("network") || msg.includes("fetch")) {
    return "تعذّر الاتصال بالخادم، تأكد من اتصالك بالإنترنت";
  }
  return "حدث خطأ، حاول مجدداً";
}

export function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signIn } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email.trim()) {
      setError("يرجى إدخال البريد الإلكتروني");
      return;
    }
    if (!password) {
      setError("يرجى إدخال كلمة المرور");
      return;
    }

    setLoading(true);
    try {
      await signIn(email, password, remember);
      navigate("/");
    } catch (err) {
      setError(friendlyError(err instanceof Error ? err.message : ""));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">مرحباً بعودتك</h2>
      <p className="text-sm text-gray-500 mb-6">سجّل دخولك للمتابعة</p>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Input
            label="البريد الإلكتروني"
            type="email"
            placeholder="ahmed@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            dir="ltr"
          />
          <p className="text-xs text-gray-400 mt-1">مثل: ahmed@gmail.com</p>
        </div>

        <Input
          label="كلمة المرور"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          dir="ltr"
        />

        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 accent-primary cursor-pointer"
          />
          <span className="text-sm text-gray-600">تذكرني</span>
        </label>

        <Button type="submit" fullWidth size="lg" disabled={loading}>
          {loading ? "جاري التسجيل..." : "تسجيل الدخول"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        ليس لديك حساب؟{" "}
        <Link to="/auth/sign-up" className="font-semibold text-sidebar hover:underline">
          إنشاء حساب جديد
        </Link>
      </p>
    </div>
  );
}
