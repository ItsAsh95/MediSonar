import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Activity, ClipboardList, Home } from 'lucide-react';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  const navLinks = [
    { path: '/', label: 'Home', icon: <Home className="w-5 h-5 mr-2" /> },
    { path: '/analyze', label: 'Symptom Analyzer', icon: <Activity className="w-5 h-5 mr-2" /> },
    { path: '/history', label: 'History', icon: <ClipboardList className="w-5 h-5 mr-2" /> },
  ];

  return (
    <header
      className={`sticky top-0 z-40 w-full transition-colors duration-300 ${
        isScrolled ? 'bg-white shadow-sm' : 'bg-transparent'
      }`}
    >
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">

          
          <Link 
            to="/" 
            className="flex items-center space-x-2 text-primary-600"
            onClick={closeMenu}
          >
            <Activity className="h-8 w-8" />
            <span className="text-xl font-bold">MediScan</span>
          </Link>

          {/* Desktop Navigation */}        
          <nav className="hidden md:flex items-center space-x-6">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center text-sm font-medium transition-colors hover:text-primary-600 ${
                  location.pathname === link.path
                    ? 'text-primary-600'
                    : 'text-gray-600'
                }`}
              >
                {link.label}
              </Link>
            ))}
            <Link
              to="/analyze"
              className="btn btn-primary"
            >
              Start Analysis
            </Link>
            <a href="/" className="text-sm font-medium text-gray-600 hover:text-primary-600">
                MediConnect
            </a>

          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden focus:outline-none"
            onClick={toggleMenu}
            aria-label="Toggle menu"
          >
            {isMenuOpen ? (
              <X className="h-6 w-6 text-gray-600" />
            ) : (
              <Menu className="h-6 w-6 text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 absolute w-full left-0 right-0 shadow-lg">
          <div className="container mx-auto px-4 py-3">
            <nav className="flex flex-col space-y-4 py-4">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center text-sm font-medium transition-colors hover:text-primary-600 ${
                    location.pathname === link.path
                      ? 'text-primary-600'
                      : 'text-gray-600'
                  }`}
                  onClick={closeMenu}
                >
                  {link.icon}
                  {link.label}
                </Link>
              ))}
              <Link
                to="/analyze"
                className="btn btn-primary w-full justify-center"
                onClick={closeMenu}
              >
                Start Analysis
              </Link>
            </nav>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;