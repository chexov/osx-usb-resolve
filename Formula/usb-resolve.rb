class UsbResolve < Formula
  desc "Resolve macOS USB devices to /dev/cu.* paths by serial number or product name"
  homepage "https://github.com/chexov/osx-usb-resolve"
  url "https://github.com/chexov/osx-usb-resolve/archive/refs/tags/v0.1.0.tar.gz"
  sha256 ""
  license "MIT"

  depends_on :macos

  def install
    bin.install "usb_resolve.py" => "usb-resolve"
  end

  test do
    assert_match "usage", shell_output("#{bin}/usb-resolve --help", 0).downcase
  end
end
