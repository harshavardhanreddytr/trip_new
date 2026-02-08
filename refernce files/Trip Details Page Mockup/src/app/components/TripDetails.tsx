import { Calendar, MapPin, ChevronRight } from 'lucide-react';
import { useState } from 'react';

interface TripDay {
  date: string;
  dayNumber: number;
  label: string;
  status: 'past' | 'today' | 'upcoming';
  location?: string;
}

export function TripDetails() {
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  const tripDays: TripDay[] = [
    {
      date: '2026-02-10',
      dayNumber: 1,
      label: 'Monday',
      status: 'past',
      location: 'Tokyo, Japan',
    },
    {
      date: '2026-02-11',
      dayNumber: 2,
      label: 'Tuesday',
      status: 'today',
      location: 'Kyoto, Japan',
    },
    {
      date: '2026-02-12',
      dayNumber: 3,
      label: 'Wednesday',
      status: 'upcoming',
      location: 'Osaka, Japan',
    },
    {
      date: '2026-02-13',
      dayNumber: 4,
      label: 'Thursday',
      status: 'upcoming',
      location: 'Nara, Japan',
    },
  ];

  const pastDays = tripDays.filter((day) => day.status === 'past');
  const todayDay = tripDays.find((day) => day.status === 'today');
  const upcomingDays = tripDays.filter((day) => day.status === 'upcoming');

  const handleDayClick = (dayNumber: number) => {
    setSelectedDay(dayNumber);
    // Navigate to day's tasks - for now just log
    console.log(`Navigating to Day ${dayNumber} tasks`);
  };

  return (
    <div className="min-h-screen bg-[#f8f7f4]">
      {/* Header */}
      <header className="bg-white border-b border-stone-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-medium text-stone-800">
                Japan Adventure
              </h1>
              <p className="text-sm text-stone-500 mt-1">
                Feb 10 – Feb 13, 2026
              </p>
            </div>
            <button className="p-2 hover:bg-stone-50 rounded-lg transition-colors">
              <Calendar className="w-5 h-5 text-stone-600" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        {/* Past Days Section */}
        {pastDays.length > 0 && (
          <div className="mb-8">
            <div className="text-xs uppercase tracking-wider text-stone-400 mb-4 pl-1">
              Past
            </div>
            <div className="space-y-2">
              {pastDays.map((day) => (
                <button
                  key={day.dayNumber}
                  onClick={() => handleDayClick(day.dayNumber)}
                  className="w-full group relative"
                >
                  <div className="bg-stone-200/40 hover:bg-stone-200/60 border border-stone-300/50 rounded-2xl p-4 transition-all duration-300 hover:shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-stone-300/60 flex items-center justify-center">
                          <span className="text-sm font-medium text-stone-600">
                            {day.dayNumber}
                          </span>
                        </div>
                        <div className="text-left">
                          <div className="text-sm font-medium text-stone-600">
                            Day {day.dayNumber}
                          </div>
                          <div className="text-xs text-stone-500">
                            {day.label}, {day.date}
                          </div>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-stone-400 group-hover:text-stone-600 transition-colors" />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Today - Hero Section */}
        {todayDay && (
          <div className="mb-12">
            <div className="text-xs uppercase tracking-wider text-[#6b7d5e] mb-4 pl-1 font-medium">
              Today
            </div>
            <button
              onClick={() => handleDayClick(todayDay.dayNumber)}
              className="w-full group relative"
            >
              <div className="bg-gradient-to-br from-[#7a8f6b] to-[#6b7d5e] rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-500 hover:scale-[1.02] border border-[#6b7d5e]/20">
                {/* Day Number Badge */}
                <div className="absolute -top-3 left-8">
                  <div className="w-14 h-14 rounded-full bg-white shadow-lg flex items-center justify-center border-4 border-[#f8f7f4]">
                    <span className="text-xl font-semibold text-[#6b7d5e]">
                      {todayDay.dayNumber}
                    </span>
                  </div>
                </div>

                <div className="mt-6 space-y-6">
                  <div>
                    <div className="text-white/80 text-sm mb-2">
                      {todayDay.label}
                    </div>
                    <div className="text-3xl font-medium text-white mb-1">
                      Day {todayDay.dayNumber}
                    </div>
                    <div className="text-lg text-white/90">{todayDay.date}</div>
                  </div>

                  {todayDay.location && (
                    <div className="flex items-center gap-2 text-white/90">
                      <MapPin className="w-5 h-5" />
                      <span className="text-base">{todayDay.location}</span>
                    </div>
                  )}

                  <div className="pt-4 flex items-center gap-2 text-white group-hover:gap-3 transition-all">
                    <span className="text-sm font-medium">View day details</span>
                    <ChevronRight className="w-5 h-5" />
                  </div>
                </div>

                {/* Decorative accent */}
                <div className="absolute -bottom-2 -right-2 w-32 h-32 bg-white/5 rounded-full blur-3xl" />
              </div>
            </button>
          </div>
        )}

        {/* Upcoming Days Section */}
        {upcomingDays.length > 0 && (
          <div>
            <div className="text-xs uppercase tracking-wider text-stone-400 mb-4 pl-1">
              Upcoming
            </div>
            <div className="space-y-4">
              {upcomingDays.map((day, index) => (
                <button
                  key={day.dayNumber}
                  onClick={() => handleDayClick(day.dayNumber)}
                  className="w-full group relative"
                  style={{
                    opacity: 1 - index * 0.15,
                  }}
                >
                  <div className="bg-white hover:bg-stone-50 border border-stone-200 rounded-2xl p-6 transition-all duration-300 hover:shadow-lg hover:border-[#7a8f6b]/30">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-full bg-[#e8ebe5] flex items-center justify-center">
                          <span className="text-base font-semibold text-[#6b7d5e]">
                            {day.dayNumber}
                          </span>
                        </div>
                        <div className="text-left">
                          <div className="text-base font-medium text-stone-800 mb-1">
                            Day {day.dayNumber}
                          </div>
                          <div className="text-sm text-stone-500 mb-2">
                            {day.label}, {day.date}
                          </div>
                          {day.location && (
                            <div className="flex items-center gap-1.5 text-stone-600">
                              <MapPin className="w-4 h-4" />
                              <span className="text-sm">{day.location}</span>
                            </div>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-stone-300 group-hover:text-[#6b7d5e] group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
