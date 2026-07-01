import { Link } from "react-router-dom";
import { useChildren } from "../../context/ChildrenContext";
import { PageHeader } from "../../components/PageHeader";
import { ChildCard } from "../../components/ChildCard";
import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { Plus } from "lucide-react";
import { useState } from "react";

export function ChildrenListPage() {
  const { children, deleteChild } = useChildren();
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const handleDelete = async () => {
    if (deleteId) {
      await deleteChild(deleteId);
      setDeleteId(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="أطفالي"
        description="إدارة ملفات أطفالك"
        action={
          <Link to="/children/add">
            <Button>
              <Plus className="h-4 w-4" />
              إضافة طفل
            </Button>
          </Link>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {children.map((child) => (
          <ChildCard
            key={child.id}
            child={child}
            onDelete={(id) => setDeleteId(id)}
          />
        ))}

        <Link
          to="/children/add"
          className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-gray-300 bg-white p-8 text-center hover:border-primary hover:bg-emerald-50/30 transition-colors min-h-[200px]"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
            <Plus className="h-7 w-7 text-gray-400" />
          </div>
          <span className="text-sm font-medium text-gray-600">إضافة طفل جديد</span>
        </Link>
      </div>

      <Modal
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        title="حذف الطفل"
      >
        <p className="text-sm text-gray-600 mb-4">
          هل أنت متأكد من حذف هذا الملف الشخصي؟ لا يمكن التراجع عن هذا الإجراء.
        </p>
        <div className="flex gap-3 justify-end">
          <Button variant="secondary" onClick={() => setDeleteId(null)}>
            إلغاء
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            حذف
          </Button>
        </div>
      </Modal>
    </div>
  );
}
