import { useState, useEffect } from "react";
import { api } from "../../lib/api";
import type { DashboardStats } from "../../types/story";
import { PageHeader } from "../../components/PageHeader";
import { Card } from "../../components/ui/Card";
import { StatCard } from "../../components/StatCard";
import { BookOpen, Flame } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";

const BEHAVIOR_AR: Record<string, string> = {
  courage: "الشجاعة",
  kindness: "اللطف",
  sharing: "المشاركة",
  honesty: "الصدق",
  responsibility: "المسؤولية",
  patience: "الصبر",
  respect: "الاحترام",
  gratitude: "الامتنان",
  other: "أخرى",
};

export function ProgressPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    api.get<DashboardStats>("/stats/").then(setStats).catch(() => {});
  }, []);

  const behaviorData =
    stats && stats.radarData.length > 0
      ? stats.radarData.map((d) => ({ behavior: BEHAVIOR_AR[d.behavior] || d.behavior, stories: d.count }))
      : [];

  const weeklyData =
    stats && stats.weeklyData.length > 0
      ? stats.weeklyData
      : [
          { day: "سبت", stories: 0 },
          { day: "أحد", stories: 0 },
          { day: "إثنين", stories: 0 },
          { day: "ثلاثاء", stories: 0 },
          { day: "أربعاء", stories: 0 },
          { day: "خميس", stories: 0 },
          { day: "جمعة", stories: 0 },
        ];

  return (
    <div>
      <PageHeader
        title="التقدم والإحصائيات"
        description="تتبع تقدم أطفالك السلوكي"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <StatCard
          label="قصص تمت قراءتها"
          value={stats?.storiesRead ?? 0}
          icon={BookOpen}
          color="text-emerald-600"
          bgColor="bg-emerald-100"
        />
        <StatCard
          label="أيام القراءة المتتالية"
          value={stats?.streak ?? 0}
          icon={Flame}
          color="text-orange-600"
          bgColor="bg-orange-100"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            قصص السلوكيات
          </h3>
          {behaviorData.length === 0 ? (
            <div className="flex items-center justify-center h-60 text-sm text-gray-400">
              لا توجد بيانات بعد — أكمل قصة لترى النتائج هنا
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={behaviorData} margin={{ top: 20, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="behavior" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  contentStyle={{ borderRadius: "8px", border: "1px solid #e2e8f0", fontSize: "14px" }}
                  formatter={(v) => [`${v} قصة`, "العدد"]}
                />
                <Bar dataKey="stories" name="قصص" fill="#30949E" radius={[6, 6, 0, 0]}>
                  <LabelList dataKey="stories" position="top" style={{ fontSize: 12, fill: "#30949E", fontWeight: 600 }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            نشاط القراءة الأسبوعي
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={weeklyData} margin={{ top: 20, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#64748b" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} />
              <Tooltip
                contentStyle={{ borderRadius: "8px", border: "1px solid #e2e8f0", fontSize: "14px" }}
                formatter={(v) => [`${v} قصة`, "القصص"]}
              />
              <Bar dataKey="stories" name="قصص" fill="#10B981" radius={[6, 6, 0, 0]}>
                <LabelList dataKey="stories" position="top" style={{ fontSize: 12, fill: "#10B981", fontWeight: 600 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}
