import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

const NotFoundPage = () => {
  return (
    <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center">
      <div className="text-center p-8">
        <h1 className="text-6xl font-bold text-primary-600 mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Page Not Found</h2>
        <p className="text-gray-600 mb-8 max-w-md mx-auto">
          The page you are looking for doesn't exist or has been moved.
        </p>
        <Link to="/" className="btn btn-primary inline-flex items-center">
          <Home className="mr-2 h-4 w-4" />
          Back to Home
        </Link>
      </div>
    </div>
  );
};

export default NotFoundPage;