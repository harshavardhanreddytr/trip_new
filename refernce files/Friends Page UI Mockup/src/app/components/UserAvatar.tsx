interface UserAvatarProps {
  name: string;
  size?: 'sm' | 'md' | 'lg';
  isOnline?: boolean;
}

export function UserAvatar({ name, size = 'md', isOnline }: UserAvatarProps) {
  const getInitials = (name: string) => {
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const getGradient = (name: string) => {
    const gradients = [
      'from-[#8fa98c] to-[#5a6f51]',
      'from-[#b8ae95] to-[#9b8e6f]',
      'from-[#a8b4a0] to-[#7a8b74]',
      'from-[#c9c0ad] to-[#a89d87]',
      'from-[#8b9a87] to-[#6b7a67]',
    ];
    const index = name.charCodeAt(0) % gradients.length;
    return gradients[index];
  };

  const sizeClasses = {
    sm: 'w-10 h-10 text-sm',
    md: 'w-12 h-12 text-base',
    lg: 'w-16 h-16 text-lg',
  };

  return (
    <div className="relative inline-block">
      <div
        className={`${sizeClasses[size]} rounded-full bg-gradient-to-br ${getGradient(
          name
        )} flex items-center justify-center text-white font-medium shadow-sm`}
      >
        {getInitials(name)}
      </div>
      {isOnline !== undefined && (
        <div
          className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-card ${
            isOnline ? 'bg-[#5a6f51]' : 'bg-[#9b9b9b]'
          }`}
        />
      )}
    </div>
  );
}
