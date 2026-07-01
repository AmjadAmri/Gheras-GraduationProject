import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useChildren } from "../../context/ChildrenContext";
import { PageHeader } from "../../components/PageHeader";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Toggle } from "../../components/ui/Toggle";
import { Select } from "../../components/ui/Select";
import { Textarea } from "../../components/ui/Textarea";
import { FileUpload } from "../../components/ui/FileUpload";
import { Button } from "../../components/ui/Button";

const ageOptions = [
  { value: "4-5", label: "4 - 5 سنوات" },
  { value: "6-7", label: "6 - 7 سنوات" },
  { value: "8-9", label: "8 - 9 سنوات" },
];

export function AddChildPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addChild, updateChild, getChild } = useChildren();

  const existingChild = id ? getChild(Number(id)) : undefined;
  const isEditing = !!existingChild;

  const [name, setName] = useState(existingChild?.name || "");
  const [gender, setGender] = useState<string>(existingChild?.gender || "boy");
  const [ageGroup, setAgeGroup] = useState(existingChild?.ageGroup || "");
  const [appearanceMethod, setAppearanceMethod] = useState<"upload" | "text">(
    existingChild?.photo ? "upload" : "text"
  );
  const [description, setDescription] = useState(existingChild?.appearanceDescription || "");
  const [photo, setPhoto] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("gender", gender);
      formData.append("ageGroup", ageGroup);
      formData.append("appearanceDescription", description);
      formData.append(
        "avatarUrl",
        `https://api.dicebear.com/9.x/adventurer/svg?seed=${name}&backgroundColor=${gender === "boy" ? "d1d4f9" : "ffd5dc"}`
      );
      if (photo) {
        formData.append("photo", photo);
      }

      if (isEditing && id) {
        await updateChild(Number(id), formData);
      } else {
        await addChild(formData);
      }
      navigate("/children");
    } catch {
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader
        title={isEditing ? "تعديل بيانات الطفل" : "إضافة طفل جديد"}
        description={isEditing ? "تعديل الملف الشخصي للطفل" : "أضف ملفاً شخصياً جديداً لطفلك"}
      />

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="اسم الطفل"
            placeholder="أدخل اسم الطفل"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <Toggle
            label="الجنس"
            options={[
              { value: "boy", label: "ولد" },
              { value: "girl", label: "بنت" },
            ]}
            value={gender}
            onChange={setGender}
          />

          <Select
            label="العمر"
            options={ageOptions}
            placeholder="اختر العمر"
            value={ageGroup}
            onChange={(e) => setAgeGroup(e.target.value)}
            required
          />

          <div className="space-y-3">
            <span className="text-sm font-medium text-gray-700">وصف المظهر</span>
            <Toggle
              options={[
                { value: "text", label: "وصف نصي" },
                { value: "upload", label: "رفع صورة" },
              ]}
              value={appearanceMethod}
              onChange={(v) => setAppearanceMethod(v as "upload" | "text")}
            />

            {appearanceMethod === "text" ? (
              <Textarea
                placeholder="صِف مظهر طفلك (لون الشعر، العيون، إلخ)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            ) : (
              <FileUpload label="صورة الطفل" onChange={setPhoto} />
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="submit" size="lg" disabled={submitting}>
              {submitting ? "جاري الحفظ..." : isEditing ? "حفظ التعديلات" : "إضافة الطفل"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="lg"
              onClick={() => navigate("/children")}
            >
              إلغاء
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
