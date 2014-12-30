package utils;

import java.io.DataOutputStream;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import android.os.RemoteException;

import com.android.uiautomator.core.UiCollection;
import com.android.uiautomator.core.UiDevice;
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public class Utils {
	public enum Orientation {
		LEFT, RIGHT, UP, DOWN
	};

	public static final String homeDir = "/storage/sdcard0";
	public static final String traceBase = homeDir + "/traces";

	public static final int SPAM_BACK = 10;

	public static void runAsRoot(String[] cmds) {
		try {
			Process p = Runtime.getRuntime().exec("su");
			DataOutputStream os = new DataOutputStream(p.getOutputStream());
			for (String tmpCmd : cmds) {
				os.writeBytes(tmpCmd + "\n");
			}
			os.writeBytes("exit\n");
			os.flush();
		} catch (Exception e) {
			e.getStackTrace();
		}
	}

	/**
	 * Create a new file in /storage/sdcard0
	 * @pre: /storage/sdcard0/random_seed_orig should be present and we need
	 *       root rights (easier for us)
	 * @param output: name of the output file
	 */
	public static void createFile(String output) {
		String[] commands = {
				"dd if=/dev/urandom of=" + homeDir + "/random_seed bs=1 count=100000",
				"cat " + homeDir + "/random_seed " + homeDir + "/random_seed_orig " + homeDir + "/random_seed > " + homeDir + "/"
						+ output };
		Utils.runAsRoot(commands);
	}

	/**
	 * Launch Tcpdump on the device and save the trace in the folder app
	 *
	 * @param app
	 *            The folder to save trace
	 */
	public static void launchTcpdump(String app, String iface) {
		long now = new Date().getTime();
		String dir = traceBase + "/" + app;
		String[] commands = {
				"mkdir -p " + dir,
				"tcpdump -i " + iface + " -w " + dir + "/"
						+ app + "_" + now + ".pcap &"
					+ " echo $! > " + traceBase + "/tcpdump.pid" };
		Utils.runAsRoot(commands);
	}

	/**
	 * Kill the tcpdump process launched
	 */
	public static void killTcpdump() {
		String[] commands = {
			"kill `cat " + traceBase + "/tcpdump.pid`",
			"rm -f " + traceBase + "/tcpdump.pid" };
		Utils.runAsRoot(commands);
	}

	/**
	 * Kill app by swiping it in the RecentApps panel
	 */
	public static boolean swipeApp(UiAutomatorTestCase t, String appText) {
		t.getUiDevice().pressHome(); // if we're already in recent apps
		try {
			t.getUiDevice().pressRecentApps();
		} catch (RemoteException e) {
			e.printStackTrace();
			return false;
		}
		t.sleep(1000);

		boolean success = false;
		UiObject app = Utils.getObjectWithText(appText);
		if (success = (app == null))
			System.out.println("Found!");
		else {
			List<UiObject> available = getElems(
					"com.android.systemui:id/recents_bg_protect",
					"com.android.systemui:id/app_label");
			for (UiObject uiObject : available) {
				try {
					if (success = (uiObject.getText().equals(appText)))
						break;
				} catch (UiObjectNotFoundException e) {
					System.out.println("App not found " + appText);
				}
			}
		}
		if (success)
			swipeToEnd(app, t.getUiDevice(), Orientation.LEFT, 10);
		t.getUiDevice().pressHome(); // go back home
		return success;
	}

	public static void customAssertTrue(UiAutomatorTestCase t, String msg,
			boolean succeeded) {
		if (!succeeded) {
			returnToHomeScreen(t);
			UiAutomatorTestCase.assertTrue("msg", false);
		}
	}

	public static void returnToHomeScreen(UiAutomatorTestCase t) {
		for (int i = 0; i < SPAM_BACK; i++) {
			t.getUiDevice().pressBack();
		}
	}
	
	public static void killApp(String packageName) {
		String[] commands = { "am force-stop " + packageName };
		Utils.runAsRoot(commands);
	}

	public static boolean openApp(UiAutomatorTestCase t, String appText,
			String packageName) throws UiObjectNotFoundException {
		// Wake up, kill app (if found) and pressHome before opening an app
		try {
			t.getUiDevice().wakeUp();
		} catch (RemoteException e1) { // not a big deal
			e1.printStackTrace();
		}
		killApp(packageName);
		t.getUiDevice().pressHome();

		UiObject allAppsButton = new UiObject(
				new UiSelector().description("Apps"));

		allAppsButton.clickAndWaitForNewWindow();

		UiScrollable appViews = new UiScrollable(
				new UiSelector().scrollable(true));

		appViews.setAsHorizontalList();
		boolean succeed = false;
		UiObject settingsApp;
		int i = 0;
		/*
		 * It seems there is a bug: flingForward ou scrollToEnd don't go to the
		 * end...
		 */
		while (!succeed) {
			try {
				settingsApp = appViews.getChildByText(new UiSelector()
						.className(android.widget.TextView.class.getName()),
						appText, i >= 14); // do not scroll, did in the catch
				succeed = true;
				settingsApp.clickAndWaitForNewWindow();
				}
			catch (UiObjectNotFoundException e) {
				// move to one new panel each time
				if (i < 7 || i >= 14)
					appViews.flingForward();
				else
					appViews.flingBackward();
			}
			if (i > 20)
				throw new UiObjectNotFoundException("App not found");
			i++;
		}

		// Validate that the package name is the expected one
		UiObject appValidation = new UiObject(
				new UiSelector().packageName(packageName));

		return appValidation.exists();
	}

	public static UiObject getObject(String id)
			throws UiObjectNotFoundException {
		UiObject obj = new UiObject(new UiSelector().resourceId(id));
		if (!obj.exists())
			throw new UiObjectNotFoundException("Object with id " + id
					+ " not found");
		return obj;
	}

	public static UiObject getObjectWithDescription(String desc) {
		return new UiObject(new UiSelector().description(desc));
	}

	public static UiObject getObjectWithId(String id, int instance) {
		return new UiObject(new UiSelector().resourceId(id).instance(instance));
	}

	public static UiObject getObjectWithId(String id) {
		return getObjectWithId(id, 0);
	}

	public static UiObject getObjectWithClassName(String className, int instance) {
		return new UiObject(new UiSelector().className(className).instance(
				instance));
	}

	public static UiObject getObjectWithClassNameAndText(String className,
			String text) {
		return new UiObject(new UiSelector().className(className).text(text));
	}

	public static UiObject getObjectWithText(String text) {
		return new UiObject(new UiSelector().text(text));
	}

	public static UiScrollable getScrollableWithId(String id) {
		return new UiScrollable(new UiSelector().resourceId(id));
	}

	public static boolean hasObject(String id) {
		try {
			return getObject(id) != null;
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean click(String id) {
		try {
			return click(getObject(id));
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean click(UiObject obj) {
		try {
			return obj.click();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	/**
	 * Click on the className UiObject containing as child the text text
	 */
	public static boolean click(UiScrollable list, String className, String text) {
		try {
			UiObject item = list.getChildByText(
					new UiSelector().className(className), text, true);
			return item.click();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean clickOnTheMiddle(UiAutomatorTestCase t) {
		return t.getUiDevice().click(t.getUiDevice().getDisplayWidth() / 2,
				t.getUiDevice().getDisplayHeight() / 2);
	}

	public static boolean clickAndWaitForNewWindow(String id) {
		try {
			return click(getObject(id));
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean clickAndWaitForNewWindow(UiObject obj) {
		try {
			return obj.clickAndWaitForNewWindow();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean clickAndWaitLoadingWindow(UiAutomatorTestCase t,
			UiObject button, String connectingId, String connectingText,
			boolean checkEnable)
			throws UiObjectNotFoundException {

		button.click(); // just start
		t.sleep(500);

		// Wait for connection, max 20 sec
		for (int i = 0; i < 40; i++) {
			if (Utils.hasObject(connectingId)
					&& Utils.hasText(connectingText, connectingText)) {
				System.out.println("Still connecting");
				t.sleep(500);
			} else if (checkEnable)
				// no object or another message, ok, we're connected if checked
				return button.isChecked();
			else
				return true;
		}
		return false;
	}

	public static boolean longClick(UiObject obj) {
		try {
			return obj.longClick();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean longClick(String id) {
		try {
			return longClick(getObject(id));
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean swipe(String id, Orientation orientation, int steps) {
		try {
			return swipe(getObject(id), orientation, steps);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean swipe(UiObject obj, Orientation orientation, int steps) {
		try {
			switch (orientation) {
			case DOWN:
				return obj.swipeDown(steps);
			case UP:
				return obj.swipeUp(steps);
			case LEFT:
				return obj.swipeLeft(steps);
			case RIGHT:
				return obj.swipeRight(steps);
			default:
				return false;
			}
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean swipeToEnd(UiObject obj, UiDevice device,
			Orientation orientation, int steps) {
		try {
			switch (orientation) {
			case DOWN:
				return obj.dragTo(obj.getBounds().centerX(),
						device.getDisplayHeight(), steps);
			case UP:
				return obj.dragTo(obj.getBounds().centerX(), 0, steps);
			case LEFT:
				return obj.dragTo(0, obj.getBounds().centerY(), steps);
			case RIGHT:
				return obj.dragTo(device.getDisplayWidth(), obj.getBounds()
						.centerY(), steps);
			default:
				return false;
			}
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	/**
	 * Set `text` to object with id `id` and clear text before
	 */
	public static boolean setText(String id, String text, boolean clear) {
		try {
			return setText(getObject(id), text, clear);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean setText(String id, String text) {
		return setText(id, text, false);
	}

	/**
	 * Set `text` to object `obj` and clear text before
	 */
	public static boolean setText(UiObject obj, String text, boolean clear) {
		try {
			if (clear)
				obj.clearTextField();
			return obj.setText(text);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean setText(UiObject obj, String text) {
		return setText(obj, text, true);
	}

	public static boolean hasText(String id, String text) {
		try {
			return hasText(getObject(id), text);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean hasText(UiObject obj, String text) {
		try {
			return obj.getText().equals(text);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean hasTextAndClick(String id, String text) {
		if (hasText(id, text))
			return click(id);
		return true;
	}

	public static boolean hasTextAndClick(UiObject obj, String text) {
		if (hasText(obj, text))
			return click(obj);
		return true;
	}

	public static boolean scrollBackward(UiScrollable obj) {
		try {
			return obj.scrollBackward();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static boolean scrollForward(UiScrollable obj) {
		try {
			return obj.scrollForward();
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}
	
	public static boolean scrollForward(UiScrollable obj, int steps) {
		try {
			return obj.scrollForward(steps);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}
	
	public static int getChildCount(UiObject obj) {
		try {
			return obj.getChildCount();
		} catch (UiObjectNotFoundException e) {
			return 0;
		}
	}
	
	public static boolean swipeLeft(UiObject obj, int steps) {
		try {
			return obj.swipeLeft(steps);
		} catch (UiObjectNotFoundException e) {
			return false;
		}
	}

	public static List<UiObject> getElems(String parentId, String childId) {
		List<UiObject> childs = new ArrayList<UiObject>();

		try {
			UiCollection parent = new UiCollection(
					new UiSelector().resourceId(parentId));
			int count = parent.getChildCount(new UiSelector()
					.resourceId(childId));

			for (int i = 0; i < count; ++i) {
				UiObject child = parent.getChild(new UiSelector().resourceId(
						childId).instance(i));
				childs.add(child);
			}
		} catch (UiObjectNotFoundException e) {
			e.printStackTrace();
		}

		return childs;
	}

	public static UiObject findCheckBoxInListWithTitle(String listViewId,
			String titleText) throws UiObjectNotFoundException {
		UiScrollable list = Utils.getScrollableWithId(listViewId);
		list.setAsVerticalList();

		while (true) {
			UiCollection listView = new UiCollection(
					new UiSelector().resourceId(listViewId));
			int count = listView.getChildCount(new UiSelector()
					.className(android.widget.LinearLayout.class.getName()));
			for (int i = 0; i < count; i++) {
				UiObject linearLayout = listView.getChild(new UiSelector()
						.className(android.widget.LinearLayout.class.getName())
						.instance(i));
				UiObject title = linearLayout.getChild(new UiSelector()
						.resourceId("android:id/title"));
				if (title.exists() && title.getText().equals(titleText))
					return linearLayout.getChild(new UiSelector()
							.resourceId("android:id/checkbox"));
			}

			if (!Utils.scrollForward(list))
				return null;
		}
	}
}
