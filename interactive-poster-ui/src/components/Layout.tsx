import ChatPanel from './ChatPanel';
import PreviewPanel from './PreviewPanel';

const Layout = () => {
  return (
    <div className="flex h-screen bg-gray-100">
      <div className="w-1/3 bg-white p-4 shadow-md flex flex-col"> {/* Added flex flex-col */}
        <ChatPanel />
      </div>
      <div className="w-2/3 bg-gray-200 p-4 flex justify-center items-start overflow-auto"> {/* Added overflow-auto */}
        <PreviewPanel />
      </div>
    </div>
  );
};
export default Layout;
