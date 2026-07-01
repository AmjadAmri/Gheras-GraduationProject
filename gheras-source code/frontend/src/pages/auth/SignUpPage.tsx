import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";

export function SignUpPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signUp } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError("");

  const normalizedEmail = email.trim().toLowerCase();

  const passwordPattern =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;

  if (!normalizedEmail.endsWith("@gmail.com")) {
  setError("يجب أن يكون البريد الإلكتروني من Gmail فقط.");
  return;
  }

  if (!passwordPattern.test(password)) {
    setError("كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل، وحرف كبير، وحرف صغير، ورقم.");
    return;
  }

  if (password !== confirmPassword) {
    setError("كلمات المرور غير متطابقة");
    return;
  }

  setLoading(true);

    try {
      await signUp(name, normalizedEmail, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل إنشاء الحساب");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">إنشاء حساب جديد</h2>
      <p className="text-sm text-gray-500 mb-6">ابدأ رحلتك مع غراس</p>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="الاسم الكامل"
          type="text"
          placeholder="أحمد محمد"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Input
          label="البريد الإلكتروني"
          type="email"
          placeholder="ahmed@gmail.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          dir="ltr"
        />
        <Input
          label="كلمة المرور"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          dir="ltr"
        />
        <Input
          label="تأكيد كلمة المرور"
          type="password"
          placeholder="••••••••"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={
            confirmPassword && password !== confirmPassword
              ? "كلمات المرور غير متطابقة"
              : undefined
          }
          dir="ltr"
        />
        <Button type="submit" fullWidth size="lg" disabled={loading}>
          {loading ? "جاري الإنشاء..." : "إنشاء الحساب"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        لديك حساب بالفعل؟{" "}
        <Link to="/auth/sign-in" className="font-semibold text-sidebar hover:underline">
          تسجيل الدخول
        </Link>
      </p>
    </div>
  );
}
